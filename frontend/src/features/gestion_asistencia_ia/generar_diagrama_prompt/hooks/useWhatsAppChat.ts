import { useState, useEffect, useRef, useCallback } from 'react';
import { useRealTimeSync, getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { getUserColor } from '../utils/chatColors';
import { calculateSafeNodePositions } from '../utils/layoutMerger';
import { callGenerateDiagramAPI, fetchAiPromptConfig, callTranscribeAudioAPI } from '../services/aiChatService';
import { mencionaADiag, comprimirImagen, leerComoDataUrl, base64DeDataUrl, MAX_IMAGEN_BYTES, MAX_AUDIO_SEGUNDOS } from '../utils/mediaChat';
import { generateDeterministicHash } from '@/features/gestion_modelado/shared/utils/hashGenerator';
import { parseUmlAttribute, parseUmlMethod } from '@/features/gestion_modelado/shared/utils/umlParser';
import { repartirRolesEquipo, asignarRolManual, type ColaboradorRolOut } from '@/features/gestion_asistencia_ia/repartir_roles';
import { repartirTareasEquipo, crearTareaManual, type TareaItem } from '@/features/gestion_asistencia_ia/repartir_tareas';
import type { ChatMessage, MediaChat, QuotedMessage, AiProvider, RoomUserMention, ParallelAiTask, PropuestaIA, SugerenciaIA } from '../types/chatTypes';
import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import { guardarVersionDespues, decidirPropuesta as decidirPropuestaAPI, PropuestaYaDecididaError, crearVersion, crearMemoria } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/services/contextoService';
import { EVENTO_MEMORIA_ACTUALIZADA } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/components/MemoriaPanel';
import { EVENTO_VERSIONES_ACTUALIZADAS } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/hooks/useVersionesContexto';
import { pausarRegistroManual, marcarOrigenProximosCambios, avisarDiagramaEstable } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/utils/registroCambios';
import { compararVersiones } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/utils/versionDiff';
import { crearComentarioElemento } from '@/features/gestion_modelado/comentar_elemento/services/comentarService';
import { detectarProblemas } from '../services/sugerenciasService';
import { crearMensajeSugerencias } from './useSugerenciasAutomaticas';
import { textoAyudaComandos } from '../components/WhatsAppChat/AyudaComandos';
import { EVENTO_SOLICITUD_IA, tomarSolicitudes, type CorreccionVinculada } from '../utils/solicitudesIA';
import { parsePeriodo, resumenHistorial, diccionarioMarkdown, descargarTexto } from '../utils/comandosIA';
import { listarVersiones } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/services/contextoService';
import { apiFetch } from '@/shared/lib/api';
import { digitalizarImagen } from '@/features/gestion_asistencia_ia/digitalizar_desde_imagen/services/digitalizarService';
import { etiquetaEsfuerzo, horasTotales } from '@/shared/utils/esfuerzo';

interface UseWhatsAppChatProps {
  codigoAcceso?: string;
  proyectoId?: number;
  proyectoNombre?: string;
}

/** Correcciones del diagrama (por clase) en el formato de la memoria de la IA */
export function correccionesDelDiagrama(
  estado: { correcciones?: Record<string, any[]> },
  nodos: Array<{ id: string; nombre: string }>
): Array<{ id: string; target: string; text: string; estado: string }> {
  const nombre = new Map(nodos.map(n => [n.id, n.nombre]));
  return Object.entries(estado.correcciones || {}).flatMap(([nodoId, lista]) =>
    (lista || []).map((c: any) => ({
      id: String(c.id),
      target: nombre.get(nodoId) || 'General',
      text: String(c.texto || ''),
      estado: c.estado === 'resuelta' ? 'resuelta' : 'abierta',
    }))
  ).filter(c => c.text);
}

export function useWhatsAppChat({ codigoAcceso = 'default', proyectoId, proyectoNombre }: UseWhatsAppChatProps) {
  const { sendChatMessage, roomUsers, cursors } = useRealTimeSync();
  const { nodes, relations, addNode, updateNode, addRelation, deleteNode, deleteRelation, getDiagramState, resolveCorreccion } = useDiagram();
  const resolveCorreccionRef = useRef(resolveCorreccion);
  resolveCorreccionRef.current = resolveCorreccion;
  // Diagrama más reciente (para guardar la versión "después" una vez aplicada la respuesta de la IA)
  const estadoActualRef = useRef({ nodes, relations });
  estadoActualRef.current = { nodes, relations };
  // Botón "Detener": una cancelación por pedido en curso (clave: id del mensaje del usuario)
  const cancelacionesRef = useRef(new Map<string, AbortController>());

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

  // Para buscar la foto/audio de un mensaje citado al mencionar a @diag
  const messagesRef = useRef<ChatMessage[]>(messages);
  messagesRef.current = messages;
  const digitalizarRef = useRef<((m: ChatMessage, dataUrl: string, nombre: string, instrucciones?: string) => Promise<void>) | null>(null);

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
      // Sin los archivos (la cuota es de ~5 MB): al reconectar, el historial del servidor los trae
      const livianos = messages.slice(-100).map(m => (m.media?.dataUrl ? { ...m, media: { ...m.media, dataUrl: '', expirado: true } } : m));
      localStorage.setItem(`chat_history_${codigoAcceso}`, JSON.stringify(livianos));
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

    // Nombres de relleno que a veces devuelve la IA (no son clases del dominio).
    // Antes la lista incluía Student, Course, Task, Notificaciones… y BORRABA esas clases reales del
    // lienzo del usuario en cada respuesta de la IA. Ahora solo se filtra lo que llega de la IA.
    const JUNK_NAMES = new Set([
      'diagrama', 'eliminadas', 'eliminada', 'borradas', 'borrada', 'clases', 'clase',
      'node', 'nodo', 'tabla', 'tablas', 'elementos'
    ]);

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
      // La IA no conoce los ids: pide borrar por {source, target} con nombres de clase
      const idDeClase = (nombre: string) =>
        nodes.find(n => n.id === nombre || (n.nombre || '').trim().toLowerCase() === nombre.trim().toLowerCase())?.id;
      result.deletedRelations.forEach((item: any) => {
        if (typeof item === 'string' || item?.id) {
          deleteRelation(typeof item === 'string' ? item : item.id);
          return;
        }
        const origen = idDeClase(String(item?.source ?? item?.from ?? ''));
        const destino = idDeClase(String(item?.target ?? item?.to ?? ''));
        if (!origen || !destino) return;
        relations
          .filter(r => (r.sourceId === origen && r.targetId === destino) || (r.sourceId === destino && r.targetId === origen))
          .forEach(r => deleteRelation(r.id));
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
  const executeParallelAi = useCallback(async (userPromptMessage: ChatMessage, extra?: { requisitos?: string }) => {
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
    const ctrl = new AbortController();
    cancelacionesRef.current.set(userPromptMessage.id, ctrl);

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

    // Si se pulsó "Detener": no se aplica ni se registra nada; toda la sala ve que se detuvo
    const finalizarDetenido = () => {
      cancelacionesRef.current.delete(userPromptMessage.id);
      const detenido: ChatMessage = {
        ...pendingAiMessage,
        text: `Detenido por ${getUserIdentity().nickname}. No se aplicó ningún cambio.`,
        aiStatus: 'cancelled',
        timestamp: Date.now()
      };
      setMessages(prev => prev.map(m => (m.id === aiMessageId ? detenido : m)));
      sendChatMessage(detenido);
      setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
    };

    try {
      const devNames = (roomUsers && roomUsers.length > 0)
        ? roomUsers.map((u: any, i: number) => u.nickname || u.nombre || `Dev ${i + 1}`).join(', ')
        : (userPromptMessage.senderName || 'Colaborador');

      // 0c. /resumen [hoy|ayer|semana|N dias|AAAA-MM-DD..AAAA-MM-DD] — CU34, sin IA
      if (command === 'resumen' && proyectoId && proyectoId > 0) {
        const periodo = parsePeriodo(userPrompt);
        let texto: string;
        try {
          const todas: any[] = [];
          let antes: number | undefined;
          for (let pag = 0; pag < 5; pag++) {
            const p = await listarVersiones(proyectoId, 100, antes);
            todas.push(...p.items);
            if (!p.hay_mas || !p.items.length || p.items[p.items.length - 1].ts < periodo.desde) break;
            antes = p.items[p.items.length - 1].id;
          }
          texto = resumenHistorial(todas, periodo);
        } catch {
          texto = 'No pude leer el historial del proyecto.';
        }
        const listo: ChatMessage = { ...pendingAiMessage, text: texto, aiStatus: 'success', timestamp: Date.now() };
        setMessages(prev => prev.map(m => (m.id === aiMessageId ? listo : m)));
        sendChatMessage(listo);
        setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
        return;
      }

      // 0d. /documentar — CU35: diccionario de datos en Markdown, sin IA
      if (command === 'documentar' || command === 'diccionario') {
        const nombre = proyectoNombre || `Proyecto ${proyectoId ?? ''}`.trim();
        const doc = diccionarioMarkdown(estadoActualRef.current, nombre);
        const archivo = `diccionario_${nombre.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'proyecto'}.md`;
        let texto: string;
        let adjunto: ChatMessage['archivo'];
        if (!doc.clases) {
          texto = 'El diagrama está vacío: no hay nada que documentar todavía.';
        } else {
          descargarTexto(archivo, doc.markdown);
          texto = `Diccionario de datos: ${doc.clases} clase${doc.clases > 1 ? 's' : ''} y ${doc.relaciones} relación${doc.relaciones === 1 ? '' : 'es'}.`;
          // adjunto para que cualquiera de la sala lo descargue (límite de tamaño razonable)
          if (doc.markdown.length <= 150000) adjunto = { nombre: archivo, contenido: doc.markdown };
        }
        const listo: ChatMessage = { ...pendingAiMessage, text: texto, aiStatus: 'success', archivo: adjunto, timestamp: Date.now() };
        setMessages(prev => prev.map(m => (m.id === aiMessageId ? listo : m)));
        sendChatMessage(listo);
        setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
        return;
      }

      // 0b. /ayuda: resumen de comandos (no llama a la IA)
      if (command === 'ayuda' || command === 'comandos' || command === 'help') {
        const ayuda: ChatMessage = { ...pendingAiMessage, text: textoAyudaComandos(), aiStatus: 'success', timestamp: Date.now() };
        setMessages(prev => prev.map(m => (m.id === aiMessageId ? ayuda : m)));
        sendChatMessage(ayuda);
        setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
        return;
      }

      // 0a. /sugerencias: revisa el diagrama ahora (detector, sin IA) y lista lo que se puede mejorar
      if (command === 'sugerencias' || command === 'sugerir') {
        const { nodes: n, relations: r } = estadoActualRef.current;
        const encontradas = await detectarProblemas(n, r);
        const base = encontradas === null
          ? { ...pendingAiMessage, text: 'No pude revisar el diagrama (¿iniciaste sesión?).', aiStatus: 'error' as const }
          : !encontradas.length
            ? { ...pendingAiMessage, text: 'Revisé el diagrama y no encontré problemas.', aiStatus: 'success' as const }
            : {
                ...crearMensajeSugerencias(encontradas.slice(0, 8), `Encontré ${encontradas.length} cosa${encontradas.length > 1 ? 's' : ''} para mejorar:`),
                id: aiMessageId,
                replyTo: pendingAiMessage.replyTo,
              };
        const listo: ChatMessage = { ...base, timestamp: Date.now() };
        setMessages(prev => prev.map(m => (m.id === aiMessageId ? listo : m)));
        sendChatMessage(listo);
        setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
        return;
      }

      // 0. /recordar …: guarda una memoria del proyecto (no llama a la IA)
      if ((command === 'recordar' || command === 'recuerda') && proyectoId && proyectoId > 0) {
        let respuesta: string;
        let estado: 'success' | 'error' = 'success';
        if (!userPrompt) {
          respuesta = 'Dime qué debo recordar. Por ejemplo:\n• /recordar los ids son UUID\n• /recordar entidades/cliente: el email es único\n• /recordar nunca borrar la clase Cliente';
          estado = 'error';
        } else {
          try {
            const m = await crearMemoria(proyectoId, { texto: userPrompt, autor: getUserIdentity().nickname });
            const tipo = m.tipo === 'restriccion' ? 'regla' : m.tipo === 'convencion' ? 'convención' : m.tipo;
            respuesta = `Lo recordaré como ${tipo} en «${m.topic_key}»:\n${m.que}`;
            window.dispatchEvent(new Event(EVENTO_MEMORIA_ACTUALIZADA));
          } catch (memErr) {
            respuesta = `No pude guardar la memoria: ${memErr instanceof Error ? memErr.message : 'error desconocido'}`;
            estado = 'error';
          }
        }
        const recordado: ChatMessage = { ...pendingAiMessage, text: respuesta, aiStatus: estado, timestamp: Date.now() };
        setMessages(prev => prev.map(m => (m.id === aiMessageId ? recordado : m)));
        sendChatMessage(recordado);
        setInFlightTasks(prev => prev.filter(t => t.taskId !== taskId));
        return;
      }

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
          if (ctrl.signal.aborted) { finalizarDetenido(); return; }

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
            text: propuestaRoles ? summaryText : `${summaryText}\n\nNo se pudo registrar la propuesta en el historial, así que no se aplicó.`,
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
          if (ctrl.signal.aborted) { finalizarDetenido(); return; }

          const createdTasks = tareasRes.tareas;
          const taskLines = createdTasks.map((t: TareaItem, i: number) => `${i + 1}. [${(t.area || t.tipo).toUpperCase()}] ${t.titulo}${t.descripcion ? ` - ${t.descripcion}` : ''}`).join('\n');
          const summaryText = `Propuesta de tareas para el equipo (${createdTasks.length}):\n\n${taskLines}`;

          const propuestaTareas = createdTasks.length
            ? await registrarPropuesta('TAREAS', userPromptMessage.text, summaryText, { tipo: 'tareas', tareas: createdTasks })
            : null;

          const completedAiMessage: ChatMessage = {
            ...pendingAiMessage,
            text: propuestaTareas || !createdTasks.length ? summaryText : `${summaryText}\n\nNo se pudo registrar la propuesta en el historial, así que no se crearon las tareas.`,
            aiStatus: propuestaTareas || !createdTasks.length ? 'success' : 'error',
            summary: summaryText,
            tasksCount: createdTasks.length,
            propuesta: propuestaTareas
              ? {
                  ...propuestaTareas,
                  tipo: 'tareas',
                  tareas: createdTasks.length,
                  lineas: [
                    ...createdTasks.map((t: TareaItem) => {
                      const esf = etiquetaEsfuerzo(t);
                      return `[${(t.area || t.tipo || 'general').toUpperCase()}] ${t.titulo}${esf ? ` (${esf})` : ''}`;
                    }),
                    ...(horasTotales(createdTasks) ? [`Total estimado: ~${horasTotales(createdTasks)} h`] : []),
                  ],
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
          relations.slice(0, 120).forEach(r => {
            const sName = idToName.get(r.sourceId) || r.sourceId;
            const tName = idToName.get(r.targetId) || r.targetId;
            let sym = '-';
            if (r.type === 'inheritance') sym = '>';
            else if (r.type === 'composition') sym = '*';
            else if (r.type === 'aggregation') sym = 'o';
            else if (r.type === 'dependency') sym = '.';
            else if (r.type === 'realization') sym = '~';
            const card = r.label && r.label !== '1..*' ? `:${r.label}` : '';
            dslParts.push(`${sName}${sym}${tName}${card}`);
          });
        }
        contextString = dslParts.join(';');
      }

      // Construcción del prompt según el comando
      let effectivePrompt = userPromptMessage.text.replace(/@diag/gi, '').trim();

      let isFixRequest = /arregl|desastre|coheren|reorganiz|limpi|corrig/i.test(effectivePrompt);
      // CU32: problemas que encuentra el detector (se muestran con "Aplicar" junto a la propuesta)
      let sugerenciasRevision: SugerenciaIA[] | undefined;

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
      } else if (command === 'revisar') {
        // CU32: detector (sin IA) + revisión de la IA; lo que corrige llega como propuesta
        const detectados = await detectarProblemas(nodes, relations);
        sugerenciasRevision = detectados?.length ? detectados.slice(0, 8) : undefined;
        const lista = (detectados || []).slice(0, 12).map(d => `- ${d.texto}: ${d.detalle}`).join('\n');
        effectivePrompt = `REVISIÓN COMPLETA DEL DIAGRAMA:\n` +
          `Revisa claves primarias y foráneas, tipos, cardinalidades, normalización, nombres y relaciones faltantes o sobrantes.\n` +
          (lista ? `Problemas ya detectados automáticamente:\n${lista}\n` : '') +
          `Devuelve en 'nodes' SOLO las clases que cambian (con todos sus atributos) y en 'relations' solo las relaciones nuevas o corregidas.\n` +
          `En 'summary' explica en viñetas breves cada problema y cómo lo corriges.\n` +
          (userPrompt ? `Foco pedido por el usuario: ${userPrompt}` : '');
      } else if (command === 'requisitos') {
        // CU36: requisitos (texto pegado o PDF) → diagrama propuesto
        const req = (extra?.requisitos || userPrompt || '').trim();
        if (!req) {
          throw new Error('Pega los requisitos después de /requisitos, o adjunta un PDF desde el menú + del chat.');
        }
        effectivePrompt = `GENERAR DIAGRAMA DESDE REQUISITOS:\n` +
          `Identifica las entidades del dominio, sus atributos (con PK y FK), métodos principales y relaciones con cardinalidad.\n` +
          `Si ya existen clases en el diagrama, reutilízalas y solo agrega o ajusta lo necesario.\n` +
          `En 'summary' resume en 2-3 oraciones qué entidades salieron de los requisitos.\n\n` +
          `REQUISITOS:\n${req.slice(0, 15000)}`;
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
        getUserIdentity().nickname,
        ctrl.signal,
        correccionesDelDiagrama(getDiagramState(), nodes)
      );
      if (ctrl.signal.aborted) { finalizarDetenido(); return; }

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
          correccion: userPromptMessage.correccion,
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
            correccion: userPromptMessage.correccion,
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
        sugerencias: sugerenciasRevision,
        usoTokens: result.uso_tokens ?? undefined,
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
      if (ctrl.signal.aborted) { finalizarDetenido(); return; }
      cancelacionesRef.current.delete(userPromptMessage.id);
      const crudo = err?.message || 'Error al procesar la solicitud.';
      // "Failed to fetch" = el servidor cortó la conexión (p. ej. nginx venció el tiempo de espera
      // de la IA o el backend se reinició): no es un fallo del diagrama.
      const errorMsg = /failed to fetch|networkerror|load failed/i.test(crudo)
        ? 'el servidor no respondió a tiempo o se cortó la conexión. Si pediste algo grande (como optimizar todo el diagrama), prueba por partes o reintenta en un momento.'
        : crudo;
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
  const sendMessage = useCallback((rawText: string, correccion?: CorreccionVinculada) => {
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
      replyTo: replyingTo || undefined,
      correccion
    };

    setMessages(prev => [...prev, newMessage]);
    sendChatMessage(newMessage);
    setReplyingTo(null);

    // Detección de invocación a @diag o comando slash (/roles, /tareas, etc.)
    if (/@diag\b/i.test(text) || /^\/[a-zA-Z0-9_-]+/i.test(text)) {
      // "@diag ..." respondiendo a una foto: la mención es explícita, la IA usa esa foto
      const citado = replyingTo ? messagesRef.current.find(m => m.id === replyingTo.id) : undefined;
      const esComando = /@diag\s+\//i.test(text) || /^\//.test(text);
      if (!esComando && citado?.media?.tipo === 'imagen' && citado.media.dataUrl && digitalizarRef.current) {
        digitalizarRef.current(newMessage, citado.media.dataUrl, citado.media.nombre || 'imagen', text.replace(/@diag/gi, '').trim());
        return;
      }
      executeParallelAi(newMessage);
    }
  }, [replyingTo, sendChatMessage, executeParallelAi]);

  /** Botón "Detener" de la burbuja de la IA (solo para quien hizo el pedido) */
  const detenerIA = useCallback((promptMessageId: string) => {
    cancelacionesRef.current.get(promptMessageId)?.abort();
  }, []);

  /** CU36: sube un PDF de requisitos, extrae el texto y pide el diagrama (llega como propuesta). */
  const enviarRequisitosPdf = useCallback(async (archivo: File): Promise<string | null> => {
    if (!/\.pdf$/i.test(archivo.name) && archivo.type !== 'application/pdf') return 'El archivo debe ser un PDF.';
    if (archivo.size > 10 * 1024 * 1024) return 'El PDF supera los 10 MB.';
    let datos: { texto: string; paginas: number; truncado: boolean };
    try {
      const base64 = await new Promise<string>((ok, mal) => {
        const lector = new FileReader();
        lector.onload = () => ok(String(lector.result));
        lector.onerror = () => mal(lector.error);
        lector.readAsDataURL(archivo);
      });
      datos = await apiFetch('/prompt/extraer-texto-pdf', {
        method: 'POST',
        body: JSON.stringify({ pdf_base64: base64, nombre: archivo.name }),
      });
    } catch (e) {
      return e instanceof Error ? e.message : 'No se pudo leer el PDF.';
    }
    const identity = getUserIdentity();
    const mensaje: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      senderId: identity.id,
      senderName: identity.nickname,
      senderColor: getUserColor(identity.id || identity.nickname),
      text: `/requisitos ${archivo.name} (${datos.paginas} pág.${datos.truncado ? ', se usó solo el inicio' : ''})`,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, mensaje]);
    sendChatMessage(mensaje);
    executeParallelAi(mensaje, { requisitos: datos.texto });
    return null;
  }, [sendChatMessage, executeParallelAi]);

  // Pedidos a @diag que llegan desde fuera del chat ("Solucionar con IA" en una corrección)
  useEffect(() => {
    const enviarPendientes = () => {
      tomarSolicitudes().forEach(s => sendMessage(`@diag ${s.texto}`, s.correccion));
    };
    enviarPendientes();   // por si el chat se abrió justo para esto
    window.addEventListener(EVENTO_SOLICITUD_IA, enviarPendientes);
    return () => window.removeEventListener(EVENTO_SOLICITUD_IA, enviarPendientes);
  }, [sendMessage]);

  // Lista de usuarios y bot para menciones (@)
  // ── Propuestas de la IA: aprobar / rechazar ───────────────────────────
  const injectRef = useRef(injectDiagramResult);
  injectRef.current = injectDiagramResult;

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
    // Comentario breve de la IA en cada clase asignada
    const quien = getUserIdentity().nickname;
    for (const r of roles) {
      for (const className of (r.clases_asignadas || []).slice(0, 10)) {
        const nodo = actuales.find(n => n.nombre?.toLowerCase() === className.toLowerCase());
        if (!nodo) continue;
        crearComentarioElemento({
          proyecto_id: proyectoId, elemento_id: nodo.id, elemento_tipo: 'node', autor_ia: true, autor_nombre: quien,
          texto: `Responsable: ${r.nombre} (${r.rol_ia || 'Desarrollador'}).`,
        }).catch(() => {});
      }
    }
    window.dispatchEvent(new Event('comentarios_actualizados'));
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
          orden: t.orden || i + 1,
          estimacion_horas: t.estimacion_horas ?? undefined,
          complejidad: t.complejidad ?? undefined
        });
      } catch (e) {
        console.warn('No se pudo crear la tarea propuesta:', t?.titulo, e);
      }
    }
    window.dispatchEvent(new Event('refetch_tareas_ia'));
    setTimeout(() => window.dispatchEvent(new Event('refetch_tareas_ia')), 800);
  }, [proyectoId]);

  /** Comentario breve de la IA en cada clase / relación que cambió al aplicar una propuesta */
  const comentarCambiosIA = useCallback(async (
    antes: { nodes: any[]; relations: any[] },
    despues: { nodes: any[]; relations: any[] },
    pedidaPor: string,
    aprobadaPor: string
  ) => {
    if (!proyectoId) return;
    const cmp = compararVersiones(antes, despues);
    const firma = pedidaPor ? ` (pedido por ${pedidaPor})` : '';
    const recortar = (xs: string[]) => xs.slice(0, 4).map(x => x.replace(/^\S+\s/, '')).join(', ') + (xs.length > 4 ? '…' : '');
    const comentarios: Array<{ id: string; tipo: 'node' | 'relation'; texto: string }> = [];
    cmp.nodos.filter(c => c.estado !== 'eliminado').slice(0, 10).forEach(c => {
      if (c.estado === 'agregado') {
        const n = c.atributos.agregados.length;
        comentarios.push({ id: c.id, tipo: 'node', texto: `Clase nueva${n ? ` con ${n} atributo${n > 1 ? 's' : ''}` : ''}${firma}.` });
        return;
      }
      const partes: string[] = [];
      if (c.renombradoDe) partes.push(`renombró ${c.renombradoDe} → ${c.nombre}`);
      const agr = [...c.atributos.agregados, ...c.metodos.agregados];
      const eli = [...c.atributos.eliminados, ...c.metodos.eliminados];
      const mod = [...c.atributos.modificados, ...c.metodos.modificados].map(m => m.despues);
      if (agr.length) partes.push(`agregó ${recortar(agr)}`);
      if (mod.length) partes.push(`cambió ${recortar(mod)}`);
      if (eli.length) partes.push(`quitó ${recortar(eli)}`);
      if (partes.length) comentarios.push({ id: c.id, tipo: 'node', texto: `${partes.join('; ')}${firma}.`.replace(/^./, s => s.toUpperCase()) });
    });
    const nombres = new Map(despues.nodes.map((x: any) => [String(x.id), x.nombre]));
    (despues.relations || []).filter((rel: any) => cmp.estadoRelacionPorId[String(rel.id)] === 'agregado').slice(0, 6).forEach((rel: any) => {
      comentarios.push({
        id: String(rel.id), tipo: 'relation',
        texto: `Relación nueva ${nombres.get(String(rel.sourceId)) ?? ''} → ${nombres.get(String(rel.targetId)) ?? ''} (${rel.type || 'association'})${firma}.`,
      });
    });
    await Promise.all(comentarios.map(c =>
      crearComentarioElemento({
        proyecto_id: proyectoId, elemento_id: c.id, elemento_tipo: c.tipo, texto: c.texto,
        autor_ia: true, autor_nombre: aprobadaPor,
      }).catch(err => console.warn('No se pudo crear el comentario de la IA:', err))
    ));
    if (comentarios.length) window.dispatchEvent(new Event('comentarios_actualizados'));
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
      // "Solucionar con IA": la corrección queda resuelta al aplicar la propuesta aprobada
      if (p.correccion) {
        resolveCorreccionRef.current(p.correccion.nodoId, p.correccion.id, `IA (aprobado por ${quien})`);
      }
      const versionId = p.versionId;
      const antesDeAplicar = { nodes: n, relations: r };
      setTimeout(async () => {
        const { nodes: n2, relations: r2 } = estadoActualRef.current;
        try {
          await guardarVersionDespues(proyectoId, versionId, { nodes: n2, relations: r2 });
        } catch (verErr) {
          console.warn('[useWhatsAppChat] No se pudo guardar la versión posterior:', verErr);
        } finally {
          window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId } }));
        }
        // CU33: la IA explica brevemente en cada elemento lo que cambió
        if (prop.tipo !== 'roles' && prop.tipo !== 'tareas') {
          await comentarCambiosIA(antesDeAplicar, { nodes: n2, relations: r2 }, msg.propuesta?.solicitadaPor || '', quien);
          // reenviar la propuesta ya aprobada: el resto de la sala refresca los comentarios
          const ultimo = messagesRef.current.find(m => m.id === messageId);
          if (ultimo) sendChatMessage(ultimo);
        }
        avisarDiagramaEstable({ nodes: n2, relations: r2 });
      }, 700);
    } else {
      window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId: p.versionId } }));
    }

    publicar({
      estado: aceptar ? 'aprobada' : 'rechazada',
      decididaPor: detalle.decidida_por || quien,
      decididaEn: Date.now(),
    });
  }, [proyectoId, sendChatMessage, aplicarRoles, crearTareasPropuestas, comentarCambiosIA]);

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

  // ── Fotos y notas de voz en el chat ──────────────────────────────────────────
  // Se comparten con la sala como cualquier mensaje. La IA NO se mete: solo actúa si alguien
  // menciona a @diag (en el texto de la foto, dicho en el audio o respondiendo a la foto/audio).

  /** Digitaliza la foto de un mensaje. Llega como PROPUESTA: nadie la aplica sin aprobar. */
  const digitalizarParaMensaje = useCallback(async (
    mensaje: ChatMessage,
    dataUrl: string,
    nombre: string,
    instrucciones?: string,
  ): Promise<void> => {
    const aiMessageId = `ai_reply_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const pendiente: ChatMessage = {
      id: aiMessageId,
      senderId: 'bot_diag',
      senderName: '@diag',
      senderColor: '#25D366',
      text: '',
      timestamp: Date.now(),
      replyTo: { id: mensaje.id, senderName: mensaje.senderName, text: mensaje.text || `📷 ${nombre}`, senderColor: mensaje.senderColor },
      isAi: true,
      aiStatus: 'pending',
      provider,
    };
    setMessages(prev => [...prev, pendiente]);
    sendChatMessage(pendiente);

    const publicar = (m: ChatMessage) => {
      setMessages(prev => prev.map(x => (x.id === aiMessageId ? m : x)));
      sendChatMessage(m);
    };

    try {
      const apiKey = provider === 'gemini' ? geminiKey : provider === 'openrouter' ? openrouterKey : provider === 'kimi' ? kimiKey : '';
      const result = await digitalizarImagen(dataUrl, instrucciones || undefined, provider, apiKey || undefined);
      const nodos = result.nodes || [];
      const relaciones = result.relations || [];

      if (nodos.length === 0) {
        publicar({ ...pendiente, text: 'No encontré clases ni tablas en la imagen. Prueba con una foto más nítida o un recorte del diagrama.', aiStatus: 'error', timestamp: Date.now() });
        return;
      }

      const resumen = `Encontré ${nodos.length} ${nodos.length === 1 ? 'elemento' : 'elementos'} y ${relaciones.length} ${relaciones.length === 1 ? 'relación' : 'relaciones'} en «${nombre}».`;
      const offset = parallelCounterRef.current++;
      const propuestaDatos = { tipo: 'diagrama', nodes: nodos, relations: relaciones, summary: resumen };
      const pedido = `Digitalizar imagen ${nombre}${instrucciones ? `: ${instrucciones}` : ''}`;

      if (proyectoId && proyectoId > 0) {
        const registrada = await registrarPropuesta('IMAGEN', pedido, resumen, propuestaDatos);
        if (!registrada) {
          publicar({ ...pendiente, text: 'Digitalicé la imagen, pero no pude registrar la propuesta en el historial, así que no se aplicó nada.', aiStatus: 'error', timestamp: Date.now() });
          return;
        }
        const existentes = new Set(estadoActualRef.current.nodes.map(n => (n.nombre || '').toLowerCase()));
        const nombres = nodos.map((n: any) => n.name || n.nombre).filter(Boolean) as string[];
        publicar({
          ...pendiente,
          text: resumen,
          aiStatus: 'success',
          timestamp: Date.now(),
          propuesta: {
            ...registrada,
            agregadas: nombres.filter(n => !existentes.has(n.toLowerCase())),
            modificadas: nombres.filter(n => existentes.has(n.toLowerCase())),
            eliminadas: [],
            relaciones: relaciones.length,
            tareas: 0,
            offset,
            refactor: false,
          },
        });
      } else {
        // Fuera de un proyecto no hay historial ni aprobación: se aplica directamente
        marcarOrigenProximosCambios({ intent: 'IMAGEN', cmd: pedido });
        await injectDiagramResult(propuestaDatos, offset, false);
        publicar({ ...pendiente, text: `${resumen} Ya están en la pizarra.`, aiStatus: 'success', timestamp: Date.now() });
      }
    } catch (err) {
      const motivo = err instanceof Error ? err.message : 'Error al digitalizar la imagen';
      publicar({ ...pendiente, text: `No pude digitalizar la imagen: ${motivo}`, aiStatus: 'error', timestamp: Date.now() });
    }
  }, [provider, geminiKey, openrouterKey, kimiKey, proyectoId, sendChatMessage, registrarPropuesta, injectDiagramResult]);
  digitalizarRef.current = digitalizarParaMensaje;

  const nuevoMensajePropio = (text: string, media: MediaChat): ChatMessage => {
    const identity = getUserIdentity();
    return {
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      senderId: identity.id,
      senderName: identity.nickname,
      senderColor: getUserColor(identity.id || identity.nickname),
      text,
      timestamp: Date.now(),
      replyTo: replyingTo || undefined,
      media,
    };
  };

  /** Foto al chat (con texto opcional). Solo si el texto menciona a @diag, la IA la digitaliza. */
  const enviarImagen = useCallback(async (archivo: File, texto: string = ''): Promise<string | null> => {
    if (!archivo.type.startsWith('image/')) return 'El archivo debe ser una imagen (PNG, JPG…).';
    if (archivo.size > MAX_IMAGEN_BYTES) return 'La imagen supera los 8 MB.';

    let foto: { dataUrl: string; mime: string };
    try {
      foto = await comprimirImagen(archivo);
    } catch {
      return 'No se pudo leer la imagen.';
    }

    const mensaje = nuevoMensajePropio(texto.trim(), { tipo: 'imagen', dataUrl: foto.dataUrl, mime: foto.mime, nombre: archivo.name });
    setMessages(prev => [...prev, mensaje]);
    sendChatMessage(mensaje);
    setReplyingTo(null);

    if (mencionaADiag(texto)) {
      const instrucciones = texto.replace(/@diag/gi, '').trim();
      await digitalizarParaMensaje(mensaje, foto.dataUrl, archivo.name, instrucciones);
    }
    return null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sendChatMessage, digitalizarParaMensaje, replyingTo]);

  /**
   * Nota de voz, con texto opcional encima (en el mismo mensaje: texto arriba, audio abajo).
   * - Sin "@diag" escrito en ese texto: es un audio normal para la sala; la IA no lo toca
   *   (ni siquiera lo transcribe).
   * - Con "@diag": va directo a la IA (se transcribe y se atiende como un "@diag ..." escrito).
   */
  const enviarAudio = useCallback(async (audio: Blob, duracion: number, texto: string = ''): Promise<string | null> => {
    if (duracion > MAX_AUDIO_SEGUNDOS + 1) return `La nota de voz supera los ${MAX_AUDIO_SEGUNDOS / 60} minutos.`;
    let dataUrl: string;
    try {
      dataUrl = await leerComoDataUrl(audio);
    } catch {
      return 'No se pudo leer el audio.';
    }
    const paraLaIA = mencionaADiag(texto);
    const mime = audio.type || 'audio/webm';
    const base = nuevoMensajePropio(texto.trim(), { tipo: 'audio', dataUrl, mime, duracion: Math.round(duracion), transcribiendo: paraLaIA });
    setMessages(prev => [...prev, base]);
    sendChatMessage(base);
    setReplyingTo(null);
    if (!paraLaIA) return null;

    let transcripcion = '';
    try {
      transcripcion = (await callTranscribeAudioAPI(base64DeDataUrl(dataUrl), mime.split(';')[0], geminiKey || null)).trim();
    } catch {
      transcripcion = '';
    }
    const actualizado: ChatMessage = { ...base, media: { ...base.media!, transcribiendo: false, transcripcion: transcripcion || undefined } };
    setMessages(prev => prev.map(m => (m.id === base.id ? actualizado : m)));
    sendChatMessage(actualizado);
    if (!transcripcion) return 'No pude entender la nota de voz para la IA (el audio se envió igual).';

    // Mismo flujo que un "@diag ..." escrito: el texto con la mención + lo dicho en el audio
    executeParallelAi({ ...actualizado, text: `${texto.trim()} ${transcripcion}` });
    return null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sendChatMessage, executeParallelAi, geminiKey, replyingTo]);

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
    decidirPropuesta,
    enviarRequisitosPdf,
    enviarImagen,
    enviarAudio,
    detenerIA
  };
}
