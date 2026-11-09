import { useState, useEffect, useRef, useCallback } from 'react';
import { useRealTimeSync, getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { getUserColor } from '../utils/chatColors';
import { calculateSafeNodePositions } from '../utils/layoutMerger';
import { callGenerateDiagramAPI, fetchAiPromptConfig } from '../services/aiChatService';
import { generateDeterministicHash } from '@/features/gestion_modelado/shared/utils/hashGenerator';
import { parseUmlAttribute, parseUmlMethod } from '@/features/gestion_modelado/shared/utils/umlParser';
import { repartirRolesEquipo, asignarRolManual, type ColaboradorRolOut } from '@/features/gestion_proyectos_asistida/repartir_roles';
import { repartirTareasEquipo, crearTareaManual, type TareaItem } from '@/features/gestion_proyectos_asistida/repartir_tareas';
import type { ChatMessage, QuotedMessage, AiProvider, RoomUserMention, ParallelAiTask, PropuestaIA } from '../types/chatTypes';
import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import { guardarVersionDespues, decidirPropuesta as decidirPropuestaAPI, PropuestaYaDecididaError, crearVersion } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/services/contextoService';
import { EVENTO_VERSIONES_ACTUALIZADAS } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/hooks/useVersionesContexto';
import { pausarRegistroManual, marcarOrigenProximosCambios } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/utils/registroCambios';

interface UseWhatsAppChatProps {
  codigoAcceso?: string;
  proyectoId?: number;
}

export function useWhatsAppChat({ codigoAcceso = 'default', proyectoId }: UseWhatsAppChatProps) {
  const { sendChatMessage, roomUsers, cursors } = useRealTimeSync();
  const { nodes, relations, addNode, updateNode, addRelation, deleteNode, deleteRelation } = useDiagram();
  // Diagrama más reciente (para guardar la versión "después" una vez aplicada la respuesta de la IA)
  const estadoActualRef = useRef({ nodes, relations });
  estadoActualRef.current = { nodes, relations };

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(`chat_history_${codigoAcceso}`);
      if (!saved) return [];
      const parsed: ChatMessage[] = JSON.parse(saved);
      return parsed.map(m => {
        if (m.isAi && m.aiStatus === 'pending') {
          return {
            ...m,
            aiStatus: 'error',
            text: 'Operación cancelada al reiniciar la sesión.'
          };
        }
        return m;
      });
    } catch {
      return [];
    }
  });

  const [provider, setProviderState] = useState<AiProvider>('gemini');

  const [geminiKey, setGeminiKeyState] = useState<string>(() => {
    return localStorage.getItem('custom_gemini_key') || '';
  });

  const [openrouterKey, setOpenrouterKeyState] = useState<string>(() => {
    return localStorage.getItem('custom_openrouter_key') || '';
  });

  const [kimiKey, setKimiKeyState] = useState<string>(() => {
    return localStorage.getItem('custom_kimi_key') || '';
  });

  const [replyingTo, setReplyingTo] = useState<QuotedMessage | null>(null);
  const [inFlightTasks, setInFlightTasks] = useState<ParallelAiTask[]>([]);
  const parallelCounterRef = useRef<number>(0);

  // Sincronizar automáticamente el proveedor activo desde .env en el backend
  useEffect(() => {
    fetchAiPromptConfig()
      .then(cfg => {
        if (cfg?.default_provider) {
          setProviderState(cfg.default_provider);
        }
      })
      .catch(() => {});
  }, []);

  // Guardar historial en localStorage
  useEffect(() => {
    try {
      localStorage.setItem(`chat_history_${codigoAcceso}`, JSON.stringify(messages.slice(-100)));
    } catch {}
  }, [messages, codigoAcceso]);

  // Escuchar mensajes entrantes por WebSocket
  useEffect(() => {
    const handleRemoteMessage = (e: Event) => {
      const customEvent = e as CustomEvent<ChatMessage>;
      if (!customEvent.detail || !customEvent.detail.id) return;
      const incoming = customEvent.detail;

      setMessages(prev => {
        const exists = prev.some(m => m.id === incoming.id);
        if (exists) {
          return prev.map(m => m.id === incoming.id ? incoming : m);
        }
        return [...prev, incoming];
      });
    };

    const handleRemoteHistory = (e: Event) => {
      const customEvent = e as CustomEvent<ChatMessage[]>;
      if (!Array.isArray(customEvent.detail)) return;
      const history = customEvent.detail;

      setMessages(prev => {
        const idMap = new Map<string, ChatMessage>();
        prev.forEach(m => idMap.set(m.id, m));
        history.forEach(m => idMap.set(m.id, m));
        return Array.from(idMap.values()).sort((a, b) => a.timestamp - b.timestamp);
      });
    };

    window.addEventListener('remote_chat_message', handleRemoteMessage);
    window.addEventListener('remote_chat_history', handleRemoteHistory);

    return () => {
      window.removeEventListener('remote_chat_message', handleRemoteMessage);
      window.removeEventListener('remote_chat_history', handleRemoteHistory);
    };
  }, []);

  const setProvider = (newProvider: AiProvider) => {
    setProviderState(newProvider);
    localStorage.setItem('ai_chat_provider', newProvider);
  };

  const setGeminiKey = (key: string) => {
    setGeminiKeyState(key);
    localStorage.setItem('custom_gemini_key', key);
  };

  const setOpenrouterKey = (key: string) => {
    setOpenrouterKeyState(key);
    localStorage.setItem('custom_openrouter_key', key);
  };

  const setKimiKey = (key: string) => {
    setKimiKeyState(key);
    localStorage.setItem('custom_kimi_key', key);
  };

  // Inyección segura de elementos al lienzo con resolución de conflictos y mapeo relacional estricto
  const injectDiagramResult = useCallback(async (result: any, offsetIndex: number, isRefactoring: boolean = false) => {
    if (!result) return;

    const JUNK_NAMES = new Set([
      'diagrama', 'eliminadas', 'eliminada', 'borradas', 'borrada', 'clases', 'clase',
      'node', 'nodo', 'tabla', 'tablas', 'elementos', 'notification', 'notifications',
      'notificaciones', 'task', 'tasks', 'assignment', 'assignments', 'student', 'students',
      'grade', 'grades', 'course', 'courses', 'teacher', 'instructor'
    ]);

    // Purga automática de nodos basura, temporales o duplicados existentes en el lienzo
    nodes.forEach(n => {
      const nameLower = (n.nombre || '').toLowerCase().trim();
      if (
        JUNK_NAMES.has(nameLower) ||
        /^node_\w+$/i.test(nameLower) ||
        nameLower === 'node_x'
      ) {
        deleteNode(n.id);
      }
    });

    // 1. Procesar eliminaciones si las hay (soporta ID exacto o Nombre de la clase)
    if (Array.isArray(result.deletedNodes)) {
      result.deletedNodes.forEach((item: any) => {
        const rawTarget = typeof item === 'string' ? item.trim() : (item.id || item.name || '').trim();
        if (!rawTarget) return;
        const matchingNodes = nodes.filter(n => 
          n.id === rawTarget || 
          (n.nombre && n.nombre.toLowerCase().trim() === rawTarget.toLowerCase())
        );
        if (matchingNodes.length > 0) {
          matchingNodes.forEach(tn => deleteNode(tn.id));
        } else {
          deleteNode(rawTarget);
        }
      });
    }

    if (Array.isArray(result.deletedRelations)) {
      result.deletedRelations.forEach((item: any) => {
        const targetId = typeof item === 'string' ? item : item.id;
        if (targetId) deleteRelation(targetId);
      });
    }

    // 2. Mapa para resolver identificadores (nombres de clases, IDs temporales o de IA) al ID real del lienzo
    const nodeMap = new Map<string, string>();
    nodes.forEach(n => {
      nodeMap.set(n.id, n.id);
      nodeMap.set(n.id.toLowerCase(), n.id);
      if (n.nombre) {
        nodeMap.set(n.nombre.trim(), n.id);
        nodeMap.set(n.nombre.trim().toLowerCase(), n.id);
      }
    });

    // 3. Filtrar nodos basura y calcular posiciones seguras sin colisiones para llamadas paralelas
    const rawIncomingNodes = (result.nodes || []).filter((n: any) => {
      const nameLower = String(n?.name || n?.nombre || '').toLowerCase().trim();
      return nameLower && !JUNK_NAMES.has(nameLower) && !/^node_\w+$/i.test(nameLower) && nameLower !== 'node_x';
    });
    const safeNodes = calculateSafeNodePositions(rawIncomingNodes, nodes, offsetIndex, isRefactoring);

    for (const node of safeNodes) {
      const rawNode = node as any;
      const rawAttrs = Array.isArray(rawNode.attributes) ? rawNode.attributes : (Array.isArray(rawNode.atributos) ? rawNode.atributos : []);
      const rawMethods = Array.isArray(rawNode.methods) ? rawNode.methods : (Array.isArray(rawNode.metodos) ? rawNode.metodos : []);
      const parsedAttrs = rawAttrs.map((attr: any) => parseUmlAttribute(attr));
      const parsedMethods = rawMethods.map((m: any) => parseUmlMethod(m));
      const nodeType = (node.type as NodeType) || 'class';

      const existing = nodes.find(n => 
        n.id === node.id || 
        (Boolean(n.nombre) && Boolean(node.name) && n.nombre.toLowerCase() === node.name.toLowerCase())
      );

      const rawResp = rawNode.responsable || rawNode.responsible || (existing ? existing.responsable : undefined);
      const rawResps = Array.isArray(rawNode.responsabilidades)
        ? rawNode.responsabilidades
        : (Array.isArray(rawNode.skills) ? rawNode.skills : (existing ? existing.responsabilidades : []));

      const hash = await generateDeterministicHash({
        nombre: node.name,
        type: nodeType,
        atributos: parsedAttrs,
        metodos: parsedMethods,
        responsable: rawResp,
        responsabilidades: rawResps
      });

      let actualNodeId = node.id;
      if (existing) {
        actualNodeId = existing.id;
        updateNode(existing.id, {
          nombre: node.name,
          type: nodeType,
          atributos: parsedAttrs,
          metodos: parsedMethods,
          responsable: rawResp,
          responsabilidades: rawResps,
          hash,
          version: existing.version + 1
        });
      } else {
        actualNodeId = node.id || `node_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
        addNode(nodeType, {
          id: actualNodeId,
          nombre: node.name,
          type: nodeType,
          atributos: parsedAttrs,
          metodos: parsedMethods,
          responsable: rawResp,
          responsabilidades: rawResps,
          x: node.x,
          y: node.y,
          width: 220,
          color: '#1e293b',
          hash,
          version: 0
        });
      }

      // Registrar mapeos en nodeMap para conectar relaciones
      if (node.id) {
        nodeMap.set(String(node.id), actualNodeId);
        nodeMap.set(String(node.id).toLowerCase(), actualNodeId);
      }
      if (node.name) {
        nodeMap.set(String(node.name), actualNodeId);
        nodeMap.set(String(node.name).toLowerCase(), actualNodeId);
      }
    }

    // 4. Conectar relaciones con resolución garantizada de IDs reales en el lienzo
    if (Array.isArray(result.relations)) {
      result.relations.forEach((rel: any) => {
        const rawSource = String(rel.sourceId || rel.source || rel.origen || rel.from || rel.src || '').trim();
        const rawTarget = String(rel.targetId || rel.target || rel.destino || rel.to || rel.dst || '').trim();
        if (!rawSource || !rawTarget) return;

        // Resolver contra nodeMap o búsqueda directa en lienzo por ID o nombre
        const sourceId = nodeMap.get(rawSource) || 
                         nodeMap.get(rawSource.toLowerCase()) || 
                         nodes.find(n => n.id === rawSource || (n.nombre && n.nombre.toLowerCase() === rawSource.toLowerCase()))?.id ||
                         rawSource;

        const targetId = nodeMap.get(rawTarget) || 
                         nodeMap.get(rawTarget.toLowerCase()) || 
                         nodes.find(n => n.id === rawTarget || (n.nombre && n.nombre.toLowerCase() === rawTarget.toLowerCase()))?.id ||
                         rawTarget;

        if (sourceId && targetId && sourceId !== targetId) {
          const relType = rel.type || rel.tipo || 'association';
          const alreadyExists = (relations || []).some(
            existingRel =>
              existingRel.id === rel.id ||
              (existingRel.sourceId === sourceId && existingRel.targetId === targetId && existingRel.type === relType)
          );
          if (!alreadyExists) {
            const isInheritance = relType === 'inheritance';
            addRelation({
              id: rel.id || `rel_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
              sourceId,
              targetId,
              type: relType,
              label: rel.targetMultiplicity || rel.label || (isInheritance ? '' : '1..*'),
              sourceLabel: rel.sourceMultiplicity || rel.sourceLabel || (isInheritance ? '' : '1'),
              version: 0,
              hash: `rel_hash_${Date.now()}`
            });
          }
        }
      });
    }

    // 5. Conexión relacional dinámica basada en claves foráneas en atributos (*entidad_id:FK)
    safeNodes.forEach(node => {
      const actualId = nodeMap.get(node.name) || nodeMap.get(node.name.toLowerCase()) || node.id;
      const rawAttrs = Array.isArray((node as any).attributes) ? (node as any).attributes : [];
      rawAttrs.forEach((attrStr: string) => {
        const fkMatch = String(attrStr).match(/\*?(\w+?)_?(?:id|Id)\s*:\s*FK/i);
        if (fkMatch && fkMatch[1]) {
          const targetName = fkMatch[1];
          const targetId = nodeMap.get(targetName) || nodeMap.get(targetName.toLowerCase());
          if (targetId && targetId !== actualId) {
            const alreadyExists = (relations || []).some(
              r => (r.sourceId === targetId && r.targetId === actualId) || (r.sourceId === actualId && r.targetId === targetId)
            );
            if (!alreadyExists) {
              addRelation({
                id: `rel_fk_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
                sourceId: targetId,
                targetId: actualId,
                type: 'association',
                label: '1..*',
                sourceLabel: '1',
                version: 0,
                hash: `rel_hash_${Date.now()}`
              });
            }
          }
        }
      });
    });
  }, [nodes, relations, addNode, updateNode, addRelation, deleteNode, deleteRelation]);

  // Ejecución asíncrona paralela de IA
  const executeParallelAi = useCallback(async (userPromptMessage: ChatMessage) => {
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const botMatch = userPromptMessage.text.match(/(?:@diag(?:\s+\/([a-zA-Z0-9_-]+))?(?:\s+([\s\S]*))?|^\/([a-zA-Z0-9_-]+)(?:\s+([\s\S]*))?)/i);
    const command = (botMatch?.[1] || botMatch?.[3] || '').toLowerCase().trim();
    const userPrompt = (botMatch?.[2] || botMatch?.[4] || '').trim();

    const activeProvider = provider;
    let activeApiKey = '';
    if (activeProvider === 'gemini') {
      activeApiKey = geminiKey;
    } else if (activeProvider === 'openrouter') {
      activeApiKey = openrouterKey;
    } else if (activeProvider === 'kimi') {
      activeApiKey = kimiKey;
    }

    const currentOffset = parallelCounterRef.current++;

    const newTask: ParallelAiTask = {
      taskId,
      promptMessageId: userPromptMessage.id,
      prompt: userPromptMessage.text,
      provider: activeProvider,
      status: 'pending',
      startTime: Date.now()
    };

    setInFlightTasks(prev => [...prev, newTask]);

    // Mensaje preliminar de la IA tipo respuesta de WhatsApp
    const aiMessageId = `ai_reply_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const pendingAiMessage: ChatMessage = {
      id: aiMessageId,
      senderId: 'bot_diag',
      senderName: '@diag',
      senderColor: '#25D366',
      text: '',
      timestamp: Date.now(),
      replyTo: {
        id: userPromptMessage.id,
        senderName: userPromptMessage.senderName,
        text: userPromptMessage.text,
        senderColor: userPromptMessage.senderColor
      },
      isAi: true,
      aiStatus: 'pending',
      provider: activeProvider
    };

    setMessages(prev => [...prev, pendingAiMessage]);
    sendChatMessage(pendingAiMessage);

    try {
      const devNames = (roomUsers && roomUsers.length > 0)
        ? roomUsers.map((u: any, i: number) => u.nickname || u.nombre || `Dev ${i + 1}`).join(', ')
        : (userPromptMessage.senderName || 'Colaborador');

      // 1. Comando /roles o /role con persistencia directa en colaboradores_proyecto y diagrama
      if ((command === 'roles' || command === 'role') && proyectoId && proyectoId > 0) {
        try {
          const getCurrentUserNumericId = (): number => {
            try {
              const stored = localStorage.getItem('user');
              if (stored) {
                const u = JSON.parse(stored);
                if (u?.id && Number(u.id) > 0) return Number(u.id);
              }
            } catch {}
            return 1;
          };

          const extractNumericId = (rawId: any, fallback: number): number => {
            if (typeof rawId === 'number' && !isNaN(rawId) && rawId > 0) return rawId;
            const digits = String(rawId || '').replace(/\D/g, '');
            if (digits) {
              const n = parseInt(digits, 10);
              if (!isNaN(n) && n > 0) return n;
            }
            return fallback;
          };

          const myNumericId = getCurrentUserNumericId();
          const myName = userPromptMessage.senderName || 'Colaborador';
          const devsList: Array<{ usuario_id: number; nombre: string; etiquetas: string[] }> = [];

          if (roomUsers && roomUsers.length > 0) {
            roomUsers.forEach((u: any, idx: number) => {
              const uid = extractNumericId(u.user_id || u.id, idx + 2);
              const nombre = u.nickname || u.nombre || `Colaborador ${idx + 1}`;
              if (!devsList.some(d => d.usuario_id === uid)) {
                devsList.push({
                  usuario_id: uid,
                  nombre,
                  etiquetas: ['modelado', 'backend', 'frontend']
                });
              }
            });
          }

          if (!devsList.some(d => d.usuario_id === myNumericId)) {
            devsList.unshift({
              usuario_id: myNumericId,
              nombre: myName,
              etiquetas: ['modelado', 'backend', 'frontend']
            });
          }

          // La IA solo PROPONE el reparto: no se guarda nada hasta que alguien apruebe
          const res = await repartirRolesEquipo({
            proyecto_id: proyectoId,
            colaboradores: devsList,
            instrucciones: userPrompt || undefined,
            provider: activeProvider,
            api_key: activeApiKey || undefined,
            persistir: false
          });

          const roleLines = res.roles.map((r: ColaboradorRolOut) =>
            `• *${r.nombre}*: ${r.rol_ia} [Áreas: ${r.areas.join(', ')}]\n  Clases: ${r.clases_asignadas.join(', ') || 'Generales'}`
          ).join('\n\n');
          const summaryText = `Propuesta de roles y áreas para el equipo:\n\n${roleLines}\n\n${res.resumen}`;

          const propuestaRoles = await registrarPropuesta(
            'ROLES', userPromptMessage.text, summaryText,
            { tipo: 'roles', roles: res.roles, resumen: res.resumen }
          );

          const completedAiMessage: ChatMessage = {
            ...pendingAiMessage,
            text: propuestaRoles ? summaryText : `${summaryText}\n\n⚠ No se pudo registrar la propuesta en el historial, así que no se aplicó.`,
            aiStatus: propuestaRoles ? 'success' : 'error',
            summary: summaryText,
            propuesta: propuestaRoles
              ? {
                  ...propuestaRoles,
                  tipo: 'roles',
                  lineas: res.roles.map((r: ColaboradorRolOut) =>
                    `${r.nombre} → ${r.rol_ia || 'Desarrollador'}${r.clases_asignadas?.length ? ` (${r.clases_asignadas.length} clase${r.clases_asignadas.length > 1 ? 's' : ''})` : ''}`
                  ),
                }
              : undefined,
            timestamp: Date.now()
          };

          setMessages(prev => prev.map(m => m.id === aiMessageId ? completedAiMessage : m));
          sendChatMessage(completedAiMessage);
          setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
          return;
        } catch (rolesErr) {
          console.warn('Fallo repartición de roles vía caso de uso repartir_roles:', rolesErr);
        }
      }

      // 2. Comando /tareas o /tasks con caso de uso dedicado repartir_tareas
      if ((command === 'tareas' || command === 'tasks') && proyectoId && proyectoId > 0) {
        try {
          const getCurrentUserNumericId = (): number => {
            try {
              const stored = localStorage.getItem('user');
              if (stored) {
                const u = JSON.parse(stored);
                if (u?.id && Number(u.id) > 0) return Number(u.id);
              }
            } catch {}
            return 1;
          };

          const extractNumericId = (rawId: any, fallback: number): number => {
            if (typeof rawId === 'number' && !isNaN(rawId) && rawId > 0) return rawId;
            const digits = String(rawId || '').replace(/\D/g, '');
            if (digits) {
              const n = parseInt(digits, 10);
              if (!isNaN(n) && n > 0) return n;
            }
            return fallback;
          };

          const myNumericId = getCurrentUserNumericId();
          const myName = userPromptMessage.senderName || 'Colaborador';
          const devsList: Array<{ usuario_id: number; nombre: string; etiquetas: string[] }> = [];

          if (roomUsers && roomUsers.length > 0) {
            roomUsers.forEach((u: any, idx: number) => {
              const uid = extractNumericId(u.user_id || u.id, idx + 2);
              const nombre = u.nickname || u.nombre || `Colaborador ${idx + 1}`;
              if (!devsList.some(d => d.usuario_id === uid)) {
                devsList.push({
                  usuario_id: uid,
                  nombre,
                  etiquetas: ['modelado', 'backend', 'frontend']
                });
              }
            });
          }

          if (!devsList.some(d => d.usuario_id === myNumericId)) {
            devsList.unshift({
              usuario_id: myNumericId,
              nombre: myName,
              etiquetas: ['modelado', 'backend', 'frontend']
            });
          }

          // La IA solo PROPONE las tareas: se crean al aprobar la propuesta
          const tareasRes = await repartirTareasEquipo({
            proyecto_id: proyectoId,
            descripcion_proyecto: userPrompt || 'Tareas de desarrollo y modelado derivadas de la arquitectura UML actual',
            colaboradores: devsList,
            provider: activeProvider,
            api_key: activeApiKey || undefined,
            persistir: false
          });

          const createdTasks = tareasRes.tareas;
          const taskLines = createdTasks.map((t: TareaItem, i: number) => `${i + 1}. [${(t.area || t.tipo).toUpperCase()}] ${t.titulo}${t.descripcion ? ` - ${t.descripcion}` : ''}`).join('\n');
          const summaryText = `Propuesta de tareas para el equipo (${createdTasks.length}):\n\n${taskLines}`;

          const propuestaTareas = createdTasks.length
            ? await registrarPropuesta('TAREAS', userPromptMessage.text, summaryText, { tipo: 'tareas', tareas: createdTasks })
            : null;

          const completedAiMessage: ChatMessage = {
            ...pendingAiMessage,
            text: propuestaTareas || !createdTasks.length ? summaryText : `${summaryText}\n\n⚠ No se pudo registrar la propuesta en el historial, así que no se crearon las tareas.`,
            aiStatus: propuestaTareas || !createdTasks.length ? 'success' : 'error',
            summary: summaryText,
            tasksCount: createdTasks.length,
            propuesta: propuestaTareas
              ? {
                  ...propuestaTareas,
                  tipo: 'tareas',
                  tareas: createdTasks.length,
                  lineas: createdTasks.map((t: TareaItem) => `[${(t.area || t.tipo || 'general').toUpperCase()}] ${t.titulo}`),
                }
              : undefined,
            timestamp: Date.now()
          };

          setMessages(prev => prev.map(m => m.id === aiMessageId ? completedAiMessage : m));
          sendChatMessage(completedAiMessage);
          setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
          return;
        } catch (taskErr) {
          console.warn('Fallo generación directa de tareas vía endpoint de tareas, reintentando con LLM:', taskErr);
        }
      }

      // Preparar contexto del diagrama actual en Hyper-DSL ultra-comprimido (máximo ahorro de tokens)
      let contextString: string | null = null;
      if (nodes && nodes.length > 0) {
        const dslParts: string[] = [];
        nodes.slice(0, 30).forEach(n => {
          const typeSuffix = n.type && n.type !== 'class' ? `:${n.type}` : '';
          const attrs = (n.atributos || [])
            .filter(a => a.nombre.toLowerCase() !== 'id')
            .map(a => {
              const t = (a.tipo || '').toLowerCase();
              if (t === 'int' || t === 'integer') return `#${a.nombre}`;
              if (t === 'float' || t === 'double' || t === 'decimal') return `$${a.nombre}`;
              if (t === 'bool' || t === 'boolean') return `?${a.nombre}`;
              if (t === 'date') return `@${a.nombre}`;
              if (t === 'datetime' || t === 'timestamp') return `^${a.nombre}`;
              if (t === 'text' || t === 'json') return `&${a.nombre}`;
              if (a.visibilidad === 'FK') return `*${a.nombre}`;
              return a.nombre;
            })
            .join(' ');

          const mets = (n.metodos || [])
            .map(m => {
              const ret = (m.retorno || 'void').toLowerCase();
              let prefix = '.';
              if (ret === 'int' || ret === 'integer') prefix = '.#';
              else if (ret === 'float' || ret === 'double') prefix = '.$';
              else if (ret === 'bool' || ret === 'boolean') prefix = '.?';
              else if (ret === 'date') prefix = '.@';
              else if (ret === 'string') prefix = '._';
              return `${prefix}${m.nombre}()`;
            })
            .join(' ');

          const nodeBody = [attrs, mets].filter(Boolean).join(' ');
          dslParts.push(`${n.nombre}${typeSuffix}${nodeBody ? ' ' + nodeBody : ''}`);
        });

        if (relations && relations.length > 0) {
          const idToName = new Map<string, string>();
          nodes.forEach(n => idToName.set(n.id, n.nombre));
          relations.slice(0, 30).forEach(r => {
            const sName = idToName.get(r.sourceId) || r.sourceId;
            const tName = idToName.get(r.targetId) || r.targetId;
            let sym = '-';
            if (r.type === 'inheritance') sym = '>';
            else if (r.type === 'composition') sym = '*';
            else if (r.type === 'aggregation') sym = 'o';
            else if (r.type === 'dependency') sym = '.';
            const card = r.label && r.label !== '1..*' ? `:${r.label}` : '';
            dslParts.push(`${sName}${sym}${tName}${card}`);
          });
        }
        contextString = dslParts.join(';');
      }

      // Construcción del prompt según el comando
      let effectivePrompt = userPromptMessage.text.replace(/@diag/gi, '').trim();

      let isFixRequest = /arregl|desastre|coheren|reorganiz|limpi|corrig/i.test(effectivePrompt);

      if (command === 'roles' || command === 'role') {
        effectivePrompt = `DISTRIBUCIÓN DE ROLES Y RESPONSABILIDADES:\n` +
          `Colaboradores presentes: ${devNames}.\n` +
          `Analiza todas las clases del diagrama y asigna roles arquitectónicos (Backend, Frontend, Base de Datos, Seguridad, Testing) a cada colaborador.\n` +
          `Actualiza las clases del diagrama asignando |resp:NombreColaborador|resps:[rol,especialidad].\n` +
          `En el campo 'summary', redacta OBLIGATORIAMENTE un desglose detallado indicando a quién se le asignó cada rol y qué clases tiene a su cargo.\n` +
          (userPrompt ? `Instrucciones adicionales: ${userPrompt}` : '');
      } else if (command === 'tareas' || command === 'tasks') {
        effectivePrompt = `GENERACIÓN DE TAREAS PARA EL EQUIPO:\n` +
          `Colaboradores disponibles: ${devNames}.\n` +
          `Genera una lista de tareas (tipo 'diagrama' o 'desarrollo') para implementar o modelar las clases.\n` +
          `Incluye el array 'tasks' con {titulo, descripcion, tipo}.\n` +
          `En el campo 'summary', redacta un resumen estructurado de las tareas generadas.\n` +
          (userPrompt ? `Instrucciones adicionales: ${userPrompt}` : '');
      } else if (command === 'optimizar') {
        isFixRequest = true;
        effectivePrompt = `OPTIMIZACIÓN Y REFACTORIZACIÓN UML:\n` +
          `Revisa todas las clases, atributos, métodos y relaciones del diagrama actual.\n` +
          `Corrige cardinalidades, elimina redundancias y normaliza el diseño orientado a objetos.\n` +
          (userPrompt ? `Instrucciones adicionales: ${userPrompt}` : '');
      } else if (command === 'explicar') {
        effectivePrompt = `EXPLICACIÓN ARQUITECTÓNICA:\n` +
          `Explica de manera didáctica y concisa la arquitectura del diagrama actual, patrones utilizados y la función de cada módulo o clase principal.\n` +
          (userPrompt ? `Pregunta del usuario: ${userPrompt}` : '');
      } else if (command === 'limpiar') {
        isFixRequest = true;
        effectivePrompt = `LIMPIEZA DE DIAGRAMA:\n` +
          `Identifica y elimina clases huérfanas, notas obsoletas o relaciones desconectadas que no aporten valor al modelo principal.\n` +
          (userPrompt ? `Instrucciones adicionales: ${userPrompt}` : '');
      } else if (command) {
        effectivePrompt = `[COMANDO /${command}]\n${userPrompt || 'Ejecutar comando sobre el diagrama actual.'}`;
      } else {
        if (isFixRequest) {
          effectivePrompt = `REFACTORIZACIÓN Y LIMPIEZA DE DIAGRAMA:\n` +
            `${effectivePrompt}\n\n` +
            `DIRECTRICES ARQUITECTÓNICAS:\n` +
            `- Reorganiza y normaliza las entidades del modelo respetando diseño orientado a objetos y patrones relacionales del dominio solicitado.\n` +
            `- Purga en 'deletedNodes' únicamente nombres exactos de entidades obsoletas o duplicadas que deban eliminarse.\n` +
            `- Cero clases huérfanas: todas las entidades deben tener relaciones lógicas (asociación, agregación, composición, herencia) con cardinalidades explícitas.`;
        }
      }

      const result = await callGenerateDiagramAPI(
        effectivePrompt,
        contextString,
        activeProvider,
        activeApiKey || null,
        proyectoId,
        { nodes, relations },          // versión anterior al cambio (historial de la IA)
        getUserIdentity().nickname
      );

      // Los cambios de la IA no se aplican solos: si el backend registró la versión,
      // quedan como PROPUESTA hasta que alguien con permiso de edición la apruebe.
      const hayCambiosIA = !!(
        result.nodes?.length || result.relations?.length ||
        result.deletedNodes?.length || result.deletedRelations?.length ||
        result.tasks?.length
      );
      let propuestaInfo: PropuestaIA | undefined;
      if (result.version_id && proyectoId && proyectoId > 0 && hayCambiosIA) {
        const existentes = new Set(nodes.map(n => (n.nombre || '').toLowerCase()));
        const nombres: string[] = (result.nodes || []).map((n: any) => n.name || n.nombre).filter(Boolean);
        propuestaInfo = {
          versionId: result.version_id,
          estado: 'pendiente',
          solicitadaPor: getUserIdentity().nickname,
          agregadas: nombres.filter(n => !existentes.has(n.toLowerCase())),
          modificadas: nombres.filter(n => existentes.has(n.toLowerCase())),
          eliminadas: (result.deletedNodes || [])
            .map((d: any) => (typeof d === 'string' ? d : d?.name || d?.id || ''))
            .filter(Boolean),
          relaciones: (result.relations || []).length,
          tareas: result.tasks?.length || 0,
          offset: currentOffset,
          refactor: isFixRequest,
        };
        window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId: result.version_id } }));
      } else if (!result.version_id && proyectoId && proyectoId > 0 && hayCambiosIA) {
        // El backend no pudo registrar la propuesta: se registra desde aquí. Si tampoco se puede,
        // no se aplica nada (la IA nunca cambia la pizarra sin aprobación).
        const registrada = await registrarPropuesta(
          'IA', userPromptMessage.text, result.summary || '',
          { tipo: 'diagrama', ...result }
        );
        if (registrada) {
          const existentes = new Set(nodes.map(n => (n.nombre || '').toLowerCase()));
          const nombres: string[] = (result.nodes || []).map((n: any) => n.name || n.nombre).filter(Boolean);
          propuestaInfo = {
            ...registrada,
            agregadas: nombres.filter(n => !existentes.has(n.toLowerCase())),
            modificadas: nombres.filter(n => existentes.has(n.toLowerCase())),
            eliminadas: (result.deletedNodes || [])
              .map((d: any) => (typeof d === 'string' ? d : d?.name || d?.id || ''))
              .filter(Boolean),
            relaciones: (result.relations || []).length,
            tareas: result.tasks?.length || 0,
            offset: currentOffset,
            refactor: isFixRequest,
          };
        } else {
          throw new Error('No se pudo registrar la propuesta en el historial, así que no se aplicaron los cambios.');
        }
      } else if (hayCambiosIA && !(proyectoId && proyectoId > 0)) {
        // Fuera de un proyecto no hay historial ni aprobación: se aplica directamente
        marcarOrigenProximosCambios({ intent: 'IA', cmd: userPromptMessage.text.replace(/@diag/gi, '').trim() });
        await injectDiagramResult(result, currentOffset, isFixRequest);
      }

      // Guardar cómo quedó la pizarra: se espera a que React aplique los cambios del lienzo
      if (!propuestaInfo && result.version_id && proyectoId && proyectoId > 0) {
        const versionId = result.version_id;
        setTimeout(async () => {
          try {
            const { nodes: n, relations: r } = estadoActualRef.current;
            await guardarVersionDespues(proyectoId, versionId, { nodes: n, relations: r });
          } catch (verErr) {
            console.warn('[useWhatsAppChat] No se pudo guardar la versión posterior:', verErr);
          } finally {
            window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId } }));
          }
        }, 700);
      }

      // Si generó tareas, persistir en base de datos para que aparezcan en el checklist
      let tasksList: any[] = Array.isArray(result.tasks) ? [...result.tasks] : [];
      if (tasksList.length === 0 && result.summary) {
        const rawLines = result.summary.split('\n');
        rawLines.forEach((line: string, i: number) => {
          const m = line.match(/^\s*(?:\d+[\.\)]|[-•*])\s*(?:\[(.*?)\])?\s*(.*?)(?:\s*[-–—:]\s*(.*))?$/);
          if (m && m[2] && m[2].trim().length > 3 && (m[1] || command === 'tareas' || command === 'tasks' || line.toLowerCase().includes('tarea') || line.toLowerCase().includes('desarrollo') || line.toLowerCase().includes('diagrama') || line.toLowerCase().includes('backend') || line.toLowerCase().includes('frontend'))) {
            const rawArea = (m[1] || 'desarrollo').toLowerCase().trim();
            tasksList.push({
              titulo: m[2].trim(),
              descripcion: m[3] ? m[3].trim() : null,
              tipo: rawArea.includes('diagrama') || rawArea.includes('modelado') ? 'diagrama' : 'desarrollo',
              area: rawArea || 'general',
              orden: i + 1
            });
          }
        });
      }

      const tasksCount = tasksList.length;
      // Con propuesta, las tareas se crean al aprobarla (no antes)
      if (tasksCount > 0 && proyectoId && proyectoId > 0 && !propuestaInfo) {
        let currentUid = 1;
        try {
          const stored = localStorage.getItem('user');
          if (stored) {
            const u = JSON.parse(stored);
            if (u?.id && Number(u.id) > 0) currentUid = Number(u.id);
          }
        } catch {}

        for (let idx = 0; idx < tasksList.length; idx++) {
          const t: any = tasksList[idx];
          try {
            await crearTareaManual({
              proyecto_id: proyectoId,
              usuario_id: currentUid,
              titulo: t.titulo || `Tarea ${idx + 1}`,
              descripcion: t.descripcion || null,
              tipo: t.tipo || 'desarrollo',
              area: t.area || 'general',
              orden: idx + 1
            });
          } catch (saveErr) {
            console.warn('Error al persistir tarea generada por IA:', saveErr);
          }
        }
        window.dispatchEvent(new Event('refetch_tareas_ia'));
        setTimeout(() => window.dispatchEvent(new Event('refetch_tareas_ia')), 800);
      }

      // Actualizar mensaje de la IA a completado con desglose legible
      let summaryText = (result.summary || '').trim();
      if (!summaryText || summaryText === '{' || summaryText.startsWith('{') || summaryText.startsWith('[')) {
        if (command === 'roles' || command === 'role') {
          const assigned = (result.nodes || []).filter((n: any) => n.responsable);
          if (assigned.length > 0) {
            summaryText = 'Distribución de roles y clases asignadas:\n\n' + assigned.map((n: any) => `• ${n.responsable}: ${n.name || n.nombre}${n.responsabilidades?.length ? ` (${n.responsabilidades.join(', ')})` : ''}`).join('\n');
          } else {
            summaryText = 'Roles y responsabilidades asignados en las clases del diagrama.';
          }
        } else if (command === 'tareas' || command === 'tasks') {
          const tList = result.tasks || [];
          if (tList.length > 0) {
            summaryText = `Tareas generadas (${tList.length}):\n\n` + tList.map((t: any, i: number) => `${i + 1}. [${(t.tipo || 'desarrollo').toUpperCase()}] ${t.titulo}`).join('\n');
          } else {
            summaryText = 'Tareas generadas para el equipo.';
          }
        } else {
          summaryText = 'Diagrama actualizado con éxito según las instrucciones.';
        }
      }

      const completedAiMessage: ChatMessage = {
        ...pendingAiMessage,
        text: summaryText,
        aiStatus: 'success',
        summary: summaryText,
        tasksCount,
        propuesta: propuestaInfo,
        timestamp: Date.now()
      };

      setMessages(prev => {
        const found = prev.some(m => m.id === aiMessageId);
        if (found) {
          return prev.map(m => m.id === aiMessageId ? completedAiMessage : m);
        }
        return [...prev, completedAiMessage];
      });
      sendChatMessage(completedAiMessage);

      setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
    } catch (err: any) {
      const errorMsg = err?.message || 'Error al procesar la solicitud.';
      const failedAiMessage: ChatMessage = {
        ...pendingAiMessage,
        text: `Error al procesar la solicitud: ${errorMsg}`,
        aiStatus: 'error',
        timestamp: Date.now()
      };

      setMessages(prev => {
        const found = prev.some(m => m.id === aiMessageId);
        if (found) {
          return prev.map(m => m.id === aiMessageId ? failedAiMessage : m);
        }
        return [...prev, failedAiMessage];
      });
      sendChatMessage(failedAiMessage);
      setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
    }
  }, [provider, geminiKey, openrouterKey, kimiKey, nodes, relations, injectDiagramResult, sendChatMessage, roomUsers, proyectoId]);

  // Enviar mensaje en el chat grupal
  const sendMessage = useCallback((rawText: string) => {
    const text = rawText.trim();
    if (!text) return;

    const identity = getUserIdentity();
    const userColor = getUserColor(identity.id || identity.nickname);

    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      senderId: identity.id,
      senderName: identity.nickname,
      senderColor: userColor,
      text,
      timestamp: Date.now(),
      replyTo: replyingTo || undefined
    };

    setMessages(prev => [...prev, newMessage]);
    sendChatMessage(newMessage);
    setReplyingTo(null);

    // Detección de invocación a @diag o comando slash (/roles, /tareas, etc.)
    if (/@diag\b/i.test(text) || /^\/[a-zA-Z0-9_-]+/i.test(text)) {
      executeParallelAi(newMessage);
    }
  }, [replyingTo, sendChatMessage, executeParallelAi]);

  // Lista de usuarios y bot para menciones (@)
  // ── Propuestas de la IA: aprobar / rechazar ───────────────────────────
  const injectRef = useRef(injectDiagramResult);
  injectRef.current = injectDiagramResult;
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const updateNodeRef = useRef(updateNode);
  updateNodeRef.current = updateNode;

  /** Registra una propuesta en el historial (pendiente). Devuelve los datos base o null si falla. */
  const registrarPropuesta = useCallback(async (
    intent: string, pedido: string, resumen: string, propuesta: Record<string, any>
  ): Promise<Pick<PropuestaIA, 'versionId' | 'estado' | 'solicitadaPor' | 'agregadas' | 'modificadas' | 'eliminadas' | 'relaciones' | 'offset' | 'refactor'> | null> => {
    if (!proyectoId || proyectoId <= 0) return null;
    const autor = getUserIdentity().nickname;
    try {
      const { nodes: n, relations: r } = estadoActualRef.current;
      const v = await crearVersion(proyectoId, {
        intent,
        cmd: pedido.replace(/@diag/gi, '').trim(),
        resumen: resumen.slice(0, 2000),
        autor,
        estado_antes: { nodes: n, relations: r },
        propuesta,
      });
      window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId: v.id } }));
      return {
        versionId: v.id, estado: 'pendiente', solicitadaPor: autor,
        agregadas: [], modificadas: [], eliminadas: [], relaciones: 0, offset: 0, refactor: false,
      };
    } catch (e) {
      console.warn('[useWhatsAppChat] No se pudo registrar la propuesta:', e);
      return null;
    }
  }, [proyectoId]);

  /** Aprobada una propuesta de roles: responsables en la pizarra y roles guardados en el proyecto */
  const aplicarRoles = useCallback(async (roles: ColaboradorRolOut[]) => {
    if (!proyectoId) return;
    const actuales = estadoActualRef.current.nodes;
    roles.forEach(r => {
      (r.clases_asignadas || []).forEach(className => {
        const nodo = actuales.find(n => n.nombre?.toLowerCase() === className.toLowerCase());
        if (nodo) {
          updateNodeRef.current(nodo.id, {
            responsable: r.nombre,
            responsabilidades: [r.rol_ia || 'Desarrollador', ...(r.areas || [])],
            version: nodo.version + 1
          });
        }
      });
    });
    for (const r of roles) {
      try {
        await asignarRolManual({
          proyecto_id: proyectoId,
          usuario_id: r.usuario_id,
          rol_ia: r.rol_ia || 'Desarrollador',
          areas: r.areas || [],
          responsabilidades: r.responsabilidades || []
        });
      } catch (e) {
        console.warn('No se pudo guardar el rol de', r.nombre, e);
      }
    }
    window.dispatchEvent(new Event('refetch_roles_ia'));
  }, [proyectoId]);

  /** Aprobada una propuesta con tareas: se crean en el proyecto */
  const crearTareasPropuestas = useCallback(async (tareas: any[]) => {
    if (!proyectoId) return;
    let uidActual = 1;
    try {
      const u = JSON.parse(localStorage.getItem('user') || 'null');
      if (u?.id && Number(u.id) > 0) uidActual = Number(u.id);
    } catch {}
    for (let i = 0; i < tareas.length; i++) {
      const t = tareas[i];
      try {
        await crearTareaManual({
          proyecto_id: proyectoId,
          usuario_id: Number(t.usuario_id) > 0 ? Number(t.usuario_id) : uidActual,
          titulo: t.titulo || `Tarea ${i + 1}`,
          descripcion: t.descripcion || null,
          tipo: t.tipo || 'desarrollo',
          area: t.area || 'general',
          orden: t.orden || i + 1
        });
      } catch (e) {
        console.warn('No se pudo crear la tarea propuesta:', t?.titulo, e);
      }
    }
    window.dispatchEvent(new Event('refetch_tareas_ia'));
    setTimeout(() => window.dispatchEvent(new Event('refetch_tareas_ia')), 800);
  }, [proyectoId]);

  const decidirPropuesta = useCallback(async (messageId: string, aceptar: boolean) => {
    const msg = messagesRef.current.find(m => m.id === messageId);
    const p = msg?.propuesta;
    if (!msg || !p || p.estado !== 'pendiente' || !proyectoId) return;

    const publicar = (cambios: Partial<PropuestaIA>) => {
      const actualizado: ChatMessage = { ...msg, propuesta: { ...p, ...cambios } };
      setMessages(prev => prev.map(m => (m.id === messageId ? actualizado : m)));
      sendChatMessage(actualizado);   // toda la sala ve la decisión
    };

    const quien = getUserIdentity().nickname;
    const { nodes: n, relations: r } = estadoActualRef.current;
    let detalle;
    try {
      detalle = await decidirPropuestaAPI(proyectoId, p.versionId, aceptar, aceptar ? { nodes: n, relations: r } : null, quien);
    } catch (err) {
      if (err instanceof PropuestaYaDecididaError) {
        // Otra persona la decidió primero: solo se refleja su decisión
        publicar({ estado: err.estado, decididaPor: err.decididaPor });
        return;
      }
      throw err;
    }

    if (aceptar && detalle.propuesta) {
      // Se aplica en la pizarra de toda la sala; la versión ya está registrada (no duplicar como manual)
      pausarRegistroManual(3000);
      const prop: any = detalle.propuesta;
      if (prop.tipo === 'roles') {
        await aplicarRoles(prop.roles || []);
      } else if (prop.tipo === 'tareas') {
        await crearTareasPropuestas(prop.tareas || []);
      } else {
        await injectRef.current(prop, p.offset ?? 0, !!p.refactor);
        if (Array.isArray(prop.tasks) && prop.tasks.length) await crearTareasPropuestas(prop.tasks);
      }
      const versionId = p.versionId;
      setTimeout(async () => {
        try {
          const { nodes: n2, relations: r2 } = estadoActualRef.current;
          await guardarVersionDespues(proyectoId, versionId, { nodes: n2, relations: r2 });
        } catch (verErr) {
          console.warn('[useWhatsAppChat] No se pudo guardar la versión posterior:', verErr);
        } finally {
          window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId } }));
        }
      }, 700);
    } else {
      window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId: p.versionId } }));
    }

    publicar({
      estado: aceptar ? 'aprobada' : 'rechazada',
      decididaPor: detalle.decidida_por || quien,
      decididaEn: Date.now(),
    });
  }, [proyectoId, sendChatMessage, aplicarRoles, crearTareasPropuestas]);

  const getMentionableUsers = useCallback((): RoomUserMention[] => {
    const mentions: RoomUserMention[] = [
      { id: 'bot_diag', name: 'diag', color: '#25D366', isAi: true }
    ];

    const seen = new Set<string>();
    seen.add('diag');

    // Añadir usuarios de la sala
    if (Array.isArray(roomUsers)) {
      roomUsers.forEach((u: any) => {
        const name = u.nickname || u.nombre;
        if (name && !seen.has(name.toLowerCase())) {
          seen.add(name.toLowerCase());
          mentions.push({
            id: u.guest_id || u.id || name,
            name,
            color: getUserColor(u.guest_id || name)
          });
        }
      });
    }

    // Añadir cursores activos
    if (cursors) {
      Object.entries(cursors).forEach(([id, c]) => {
        if (c.nickname && !seen.has(c.nickname.toLowerCase())) {
          seen.add(c.nickname.toLowerCase());
          mentions.push({
            id,
            name: c.nickname,
            color: getUserColor(id)
          });
        }
      });
    }

    return mentions;
  }, [roomUsers, cursors]);

  return {
    messages,
    provider,
    setProvider,
    geminiKey,
    setGeminiKey,
    openrouterKey,
    setOpenrouterKey,
    kimiKey,
    setKimiKey,
    replyingTo,
    setReplyingTo,
    sendMessage,
    inFlightTasks,
    getMentionableUsers,
    decidirPropuesta
  };
}
