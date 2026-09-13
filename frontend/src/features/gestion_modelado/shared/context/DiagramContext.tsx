import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import type { ClassNode, DiagramState, Atributo, Metodo, Relation, RelationType, NodeType, Correccion } from '../types/types';
import { useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { offlineSyncService } from '@/features/gestion_concurrencia/sincronizar_estado_local/services/OfflineSyncService';
import { generateDeterministicHash } from '../utils/hashGenerator';
import { syncOnReconnect, type ConflictItem, type ClassVersionSnapshot } from '../utils/VersionManager';

function uid() {
  return Math.random().toString(36).substr(2, 9);
}

// ─── Tipos del contexto ──────────────────────────────────────────────────────

interface DiagramContextType {
  nodes: ClassNode[];
  relations: Relation[];
  correcciones: Record<string, Correccion[]>;
  isOffline: boolean;
  conflicts: ConflictItem[];
  selectedIds: string[];
  connectingSource: string | null;   // CU9: ID del nodo que está siendo el origen de una conexión
  activeTool: string;
  setSelectedIds: (ids: string[]) => void;
  setActiveTool: (tool: string) => void;
  // CU8: Insertar elemento
  addNode: (type?: NodeType, node?: ClassNode, isRemote?: boolean) => void;
  updateNode: (id: string, partial: Partial<ClassNode>, isRemote?: boolean) => void;
  deleteNode: (id: string, isRemote?: boolean) => void;
  moveNode: (id: string, x: number, y: number, isRemote?: boolean) => void;
  // CU9: Conectar elementos
  startConnect: (sourceId: string) => void;
  finishConnect: (targetId: string, type: RelationType) => void;
  cancelConnect: () => void;
  updateRelation: (id: string, partial: Partial<Relation>, isRemote?: boolean) => void;
  deleteRelation: (id: string, isRemote?: boolean) => void;
  // Atributos y Métodos
  addAtributo: (nodeId: string, attr?: Atributo, isRemote?: boolean) => void;
  updateAtributo: (nodeId: string, attrId: string, partial: Partial<Atributo>, isRemote?: boolean) => void;
  deleteAtributo: (nodeId: string, attrId: string, isRemote?: boolean) => void;
  addMetodo: (nodeId: string, met?: Metodo, isRemote?: boolean) => void;
  updateMetodo: (nodeId: string, metodId: string, partial: Partial<Metodo>, isRemote?: boolean) => void;
  deleteMetodo: (nodeId: string, metodId: string, isRemote?: boolean) => void;
  // Correcciones
  addCorreccion: (targetId: string, texto: string, autorNombre: string, remoteCorr?: Correccion, isRemote?: boolean) => void;
  resolveCorreccion: (targetId: string, correccionId: string, resueltoPorNombre: string, isRemote?: boolean) => void;
  
  resolveConflict: (nodeId: string, field: string, keepLocal: boolean) => void;
  getDiagramState: () => DiagramState;
  loadDiagram: (state: DiagramState) => void;
  isDirty: React.MutableRefObject<boolean>;
}

const DiagramContext = createContext<DiagramContextType | null>(null);

// ─── Helper: calcula el hash semántico de una clase (sin x,y) ───────────────

async function computeClassHash(node: ClassNode): Promise<string> {
  const payload = {
    nombre: node.nombre,
    color: node.color,
    atributos: node.atributos.map(a => ({
      id: a.id, visibilidad: a.visibilidad, nombre: a.nombre, tipo: a.tipo, version: a.version
    })),
    metodos: node.metodos.map(m => ({
      id: m.id, visibilidad: m.visibilidad, nombre: m.nombre, parametros: m.parametros, retorno: m.retorno, version: m.version
    })),
  };
  return generateDeterministicHash(payload);
}

// ─── Helper: clona un nodo, sube la versión de clase y recalcula hash ────────
// IMPORTANTE: Esta función es async pero retorna el nodo completo ANTES de
// pasarlo a setNodes. Así React nunca recibe una Promesa como valor de estado.

async function bumpVersion(node: ClassNode, isOffline: boolean): Promise<ClassNode> {
  const newVersion = node.version + 1;
  const updated = { ...node, version: newVersion };
  const newHash = await computeClassHash(updated);
  return {
    ...updated,
    hash: newHash,
    isOfflineDirty: isOffline ? true : node.isOfflineDirty,
  };
}

// ─── Helper: emitir delta al offlineSyncService e IndexedDB ─────────────────────────

async function saveToofflineSyncService(node: ClassNode): Promise<Record<string, any>> {
  const objects: Record<string, any> = {};

  for (const attr of node.atributos) {
    const obj = { type: 'attribute', data: attr };
    const h = await generateDeterministicHash(obj);
    objects[h] = obj;
    offlineSyncService.putObject(h, obj as any);
  }
  for (const met of node.metodos) {
    const obj = { type: 'method', data: met };
    const h = await generateDeterministicHash(obj);
    objects[h] = obj;
    offlineSyncService.putObject(h, obj as any);
  }
  const classObj = { type: 'class', data: node };
  objects[node.hash] = classObj;
  offlineSyncService.putObject(node.hash, classObj as any);

  return objects;
}

// ─── Provider ───────────────────────────────────────────────────────────────

export const DiagramProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [nodes, setNodes] = useState<ClassNode[]>([]);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [correcciones, setCorrecciones] = useState<Record<string, Correccion[]>>({});
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activeTool, setActiveTool] = useState<string>('select');
  const [connectingSource, setConnectingSource] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const isDirty = useRef(false);
  const { broadcastDiagramEvent, broadcastDiagramDelta } = useRealTimeSync();

  const mark = useCallback(() => { isDirty.current = true; }, []);

  // ── Detectar cambios de conectividad ─────────────────────────────────────

  useEffect(() => {
    const goOffline = () => {
      setIsOffline(true);
      setNodes(prev => prev.map(n => ({
        ...n,
        offlineVersion: n.offlineVersion ?? n.version,
      })));
      console.warn('[VCS] Modo offline — versiones congeladas');
    };

    const goOnline = () => {
      setIsOffline(false);
      console.log('[VCS] Volviendo online — solicitando sincronización...');
      window.dispatchEvent(new CustomEvent('vcs_request_sync'));
    };

    window.addEventListener('offline', goOffline);
    window.addEventListener('online', goOnline);
    return () => {
      window.removeEventListener('offline', goOffline);
      window.removeEventListener('online', goOnline);
    };
  }, []);

  // ── Recibir snapshots del servidor y hacer el diff ───────────────────────

  useEffect(() => {
    const handleServerSync = (e: any) => {
      const serverSnapshots: ClassVersionSnapshot[] = e.detail?.snapshots ?? [];
      if (!serverSnapshots.length) return;
      setNodes(prev => {
        const result = syncOnReconnect(prev, serverSnapshots);
        if (result.conflicts.length > 0) setConflicts(result.conflicts);
        return result.applied;
      });
    };

    window.addEventListener('vcs_server_sync', handleServerSync);
    return () => window.removeEventListener('vcs_server_sync', handleServerSync);
  }, []);

  // ── Resolver conflicto ───────────────────────────────────────────────────

  const resolveConflict = useCallback((nodeId: string, field: string, keepLocal: boolean) => {
    const conflict = conflicts.find(c => c.nodeId === nodeId && c.field === field);
    if (conflict && keepLocal) {
      const [kind, itemId, prop] = field.split(':');
      setNodes(prev => prev.map(n => {
        if (n.id !== nodeId) return n;
        if (kind === 'attr') {
          return { ...n, atributos: n.atributos.map(a => a.id === itemId ? { ...a, [prop]: conflict.localValue } : a) };
        }
        if (kind === 'met') {
          return { ...n, metodos: n.metodos.map(m => m.id === itemId ? { ...m, [prop]: conflict.localValue } : m) };
        }
        return n;
      }));
    }
    setConflicts(prev => prev.filter(c => !(c.nodeId === nodeId && c.field === field)));
  }, [conflicts]);

  // ── CRUD — patrón correcto: compute async PRIMERO, luego setNodes sync ───

  const addNode = useCallback((type: NodeType = 'class', remoteNode?: ClassNode, isRemote = false) => {
    if (type === 'port' && !isRemote) {
      const hasPart = nodes.some(n => n.type === 'part');
      if (!hasPart) {
        alert('No se puede crear un Port sin un Part existente.');
        return;
      }
    }
    const NO_ATTRS = ['note', 'enum', 'port', 'expose_interface', 'create_event', 'destroy_event', 'constraint', 'text', 'boundary', 'part'];
    const NO_METS  = ['note', 'enum', 'port', 'expose_interface', 'create_event', 'destroy_event', 'constraint', 'text', 'boundary', 'part'];
    const baseAttrs: Atributo[] = !NO_ATTRS.includes(type)
      ? [{ id: uid(), visibilidad: '-', nombre: 'atributo', tipo: 'int', version: 0 }]
      : [];
    const baseMets: Metodo[] = !NO_METS.includes(type)
      ? [{ id: uid(), visibilidad: '+', nombre: 'operacion', parametros: '', retorno: 'void', version: 0 }]
      : [];
    const colorMap: Record<NodeType, string> = {
      class: '#ed8936',
      interface: '#b794f4',
      abstract: '#ed8936',
      enum: '#68d391',
      datatype: '#ecc94b',
      primitive: '#a3e635',
      signal: '#fefcbf',
      note: '#f6e05e',
      part: '#ecc94b',
      port: '#ed8936',
      expose_interface: '#9f7aea',
      auxillary: '#4a7fd4',
      focus: '#4a7fd4',
      implementation_class: '#4a7fd4',
      realization_class: '#4a7fd4',
      specification: '#4a7fd4',
      type: '#4a7fd4',
      utility: '#4a7fd4',
      create_event: '#6a1b9a',
      destroy_event: '#6a1b9a',
      constraint: '#f56565',
      text: '#a0aec0',
      artifact: '#4299e1',
      requirement: '#ed8936',
      issue: '#e53e3e',
      change: '#ed8936',
      information_item: '#4fd1c5',
      boundary: '#718096'
    };

    const base: ClassNode = remoteNode || {
      id: uid(),
      type,
      x: 120 + Math.random() * 300,
      y: 100 + Math.random() * 200,
      width: 220,
      nombre: type === 'note' ? 'Nota' : type === 'enum' ? 'Enum' : type === 'interface' ? 'IInterfaz' : 'NuevaClase',
      color: colorMap[type],
      version: 0,
      hash: '',
      atributos: baseAttrs,
      metodos: baseMets,
      valores: type === 'enum' ? ['VALOR_1', 'VALOR_2'] : undefined,
      contenido: type === 'note' ? 'Escribir nota...' : undefined,
    };

    // Calcular hash async y luego actualizar estado de forma segura
    computeClassHash(base).then(hash => {
      const node: ClassNode = { ...base, hash };
      setNodes(prev => [...prev, node]);
      if (!isRemote) {
        setSelectedIds([node.id]);
        broadcastDiagramEvent({ action: 'addNode', payload: { node } });
        if (!isOffline) {
          saveToofflineSyncService(node).then(objects => {
            broadcastDiagramDelta(node.hash, objects);
          });
        }
      }
    });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);


  const updateRelation = useCallback((id: string, partial: Partial<Relation>, isRemote = false) => {
    setRelations(prev => prev.map(r => r.id === id ? { ...r, ...partial, version: r.version + 1 } : r));
    if (!isRemote) broadcastDiagramEvent({ action: 'updateRelation', payload: { id, partial } });
    mark();
  }, [broadcastDiagramEvent, mark]);

  const deleteRelation = useCallback((id: string, isRemote = false) => {
    setRelations(prev => prev.filter(r => r.id !== id));
    if (!isRemote) broadcastDiagramEvent({ action: 'deleteRelation', payload: { id } });
    mark();
  }, [broadcastDiagramEvent, mark]);

  const updateNode = useCallback((id: string, partial: Partial<ClassNode>, isRemote = false) => {
    setNodes(prev => {
      const current = prev.find(n => n.id === id);
      if (!current) return prev;
      return prev.map(n => n.id === id ? { ...current, ...partial } : n);
    });

    const current = nodes.find(n => n.id === id);
    if (!current) return;
    const updated = { ...current, ...partial };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === id ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => {
          broadcastDiagramDelta(bumped.hash, objects);
        });
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'updateNode', payload: { id, partial } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  const deleteNode = useCallback((id: string, isRemote = false) => {
    setNodes(prev => prev.filter(n => n.id !== id));
    if (!isRemote) {
      setSelectedIds(sel => sel.filter(s => s !== id));
      broadcastDiagramEvent({ action: 'deleteNode', payload: { id } });
    }
    mark();
  }, [mark, broadcastDiagramEvent]);

  // Mover NO sube versión — es posición visual efímera
  const moveNode = useCallback((id: string, x: number, y: number, isRemote = false) => {
    setNodes(prev => prev.map(n => n.id === id ? { ...n, x, y } : n));
    if (!isRemote) broadcastDiagramEvent({ action: 'moveNode', payload: { id, x, y } });
  }, [broadcastDiagramEvent]);

  const addAtributo = useCallback((nodeId: string, remoteAttr?: Atributo, isRemote = false) => {
    const attr: Atributo = remoteAttr || { id: uid(), visibilidad: '-', nombre: 'atributo', tipo: 'String', version: 0 };

    setNodes(prev => {
      const current = prev.find(n => n.id === nodeId);
      if (!current) return prev;
      return prev.map(n => n.id === nodeId ? { ...current, atributos: [...current.atributos, attr] } : n);
    });

    const current = nodes.find(n => n.id === nodeId);
    if (!current) return;
    const updated = { ...current, atributos: [...current.atributos, attr] };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === nodeId ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => broadcastDiagramDelta(bumped.hash, objects));
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'addAtributo', payload: { nodeId, attr } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  const updateAtributo = useCallback((nodeId: string, attrId: string, partial: Partial<Atributo>, isRemote = false) => {
    setNodes(prev => {
      const current = prev.find(n => n.id === nodeId);
      if (!current) return prev;
      const updatedAttrs = current.atributos.map(a => a.id === attrId ? { ...a, ...partial, version: a.version + 1 } : a);
      return prev.map(n => n.id === nodeId ? { ...current, atributos: updatedAttrs } : n);
    });

    const current = nodes.find(n => n.id === nodeId);
    if (!current) return;
    const updatedAttrs = current.atributos.map(a => a.id === attrId ? { ...a, ...partial, version: a.version + 1 } : a);
    const updated = { ...current, atributos: updatedAttrs };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === nodeId ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => broadcastDiagramDelta(bumped.hash, objects));
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'updateAtributo', payload: { nodeId, attrId, partial } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  const deleteAtributo = useCallback((nodeId: string, attrId: string, isRemote = false) => {
    setNodes(prev => {
      const current = prev.find(n => n.id === nodeId);
      if (!current) return prev;
      return prev.map(n => n.id === nodeId ? { ...current, atributos: current.atributos.filter(a => a.id !== attrId) } : n);
    });

    const current = nodes.find(n => n.id === nodeId);
    if (!current) return;
    const updated = { ...current, atributos: current.atributos.filter(a => a.id !== attrId) };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === nodeId ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => broadcastDiagramDelta(bumped.hash, objects));
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'deleteAtributo', payload: { nodeId, attrId } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  const addMetodo = useCallback((nodeId: string, remoteMet?: Metodo, isRemote = false) => {
    const met: Metodo = remoteMet || { id: uid(), visibilidad: '+', nombre: 'metodo', parametros: '', retorno: 'void', version: 0 };

    setNodes(prev => {
      const current = prev.find(n => n.id === nodeId);
      if (!current) return prev;
      return prev.map(n => n.id === nodeId ? { ...current, metodos: [...current.metodos, met] } : n);
    });

    const current = nodes.find(n => n.id === nodeId);
    if (!current) return;
    const updated = { ...current, metodos: [...current.metodos, met] };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === nodeId ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => broadcastDiagramDelta(bumped.hash, objects));
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'addMetodo', payload: { nodeId, met } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  const updateMetodo = useCallback((nodeId: string, metodId: string, partial: Partial<Metodo>, isRemote = false) => {
    setNodes(prev => {
      const current = prev.find(n => n.id === nodeId);
      if (!current) return prev;
      const updatedMets = current.metodos.map(m => m.id === metodId ? { ...m, ...partial, version: m.version + 1 } : m);
      return prev.map(n => n.id === nodeId ? { ...current, metodos: updatedMets } : n);
    });

    const current = nodes.find(n => n.id === nodeId);
    if (!current) return;
    const updatedMets = current.metodos.map(m => m.id === metodId ? { ...m, ...partial, version: m.version + 1 } : m);
    const updated = { ...current, metodos: updatedMets };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === nodeId ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => broadcastDiagramDelta(bumped.hash, objects));
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'updateMetodo', payload: { nodeId, metodId, partial } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  const deleteMetodo = useCallback((nodeId: string, metodId: string, isRemote = false) => {
    setNodes(prev => {
      const current = prev.find(n => n.id === nodeId);
      if (!current) return prev;
      return prev.map(n => n.id === nodeId ? { ...current, metodos: current.metodos.filter(m => m.id !== metodId) } : n);
    });

    const current = nodes.find(n => n.id === nodeId);
    if (!current) return;
    const updated = { ...current, metodos: current.metodos.filter(m => m.id !== metodId) };

    bumpVersion(updated, isOffline).then(bumped => {
      setNodes(latest => latest.map(n => n.id === nodeId ? bumped : n));
      if (!isRemote && !isOffline) {
        saveToofflineSyncService(bumped).then(objects => broadcastDiagramDelta(bumped.hash, objects));
      }
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'deleteMetodo', payload: { nodeId, metodId } });
    mark();
  }, [nodes, mark, broadcastDiagramEvent, broadcastDiagramDelta, isOffline]);

  // ── Correcciones ─────────────────────────────────────────────────────────

  const addCorreccion = useCallback((targetId: string, texto: string, autorNombre: string, remoteCorr?: Correccion, isRemote = false) => {
    const corr: Correccion = remoteCorr || {
      id: uid(),
      targetId,
      texto,
      autorId: 0, 
      autorNombre,
      fecha: Date.now(),
      estado: 'abierta'
    };
    
    setCorrecciones(prev => {
      const current = prev[targetId] || [];
      return { ...prev, [targetId]: [...current, corr] };
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'addCorreccion', payload: { targetId, texto, autorNombre, corr } });
    mark();
  }, [broadcastDiagramEvent, mark]);

  const resolveCorreccion = useCallback((targetId: string, correccionId: string, resueltoPorNombre: string, isRemote = false) => {
    setCorrecciones(prev => {
      const current = prev[targetId] || [];
      const updated = current.map(c => c.id === correccionId ? { ...c, estado: 'resuelta' as const, fechaResolucion: Date.now(), resueltoPorNombre } : c);
      return { ...prev, [targetId]: updated };
    });

    if (!isRemote) broadcastDiagramEvent({ action: 'resolveCorreccion', payload: { targetId, correccionId, resueltoPorNombre } });
    mark();
  }, [broadcastDiagramEvent, mark]);

  // ── Conexiones y Relaciones ──────────────────────────────────────────────

  // CU9: Iniciar conexión — el usuario selecciona el nodo origen
  const startConnect = useCallback((sourceId: string) => {
    setConnectingSource(sourceId);
    setSelectedIds([]);
  }, []);

  // CU9: Finalizar conexión — el usuario selecciona el nodo destino y el tipo
  const finishConnect = useCallback((targetId: string, type: RelationType) => {
    const isSelfLoopAllowed = ['delegate', 'assembly', 'connector', 'association'].includes(type);
    if (!connectingSource || (connectingSource === targetId && !isSelfLoopAllowed)) {
      setConnectingSource(null);
      return;
    }

    const srcNode = nodes.find(n => n.id === connectingSource);
    const tgtNode = nodes.find(n => n.id === targetId);

    if (!srcNode || !tgtNode) {
      setConnectingSource(null);
      return;
    }

    const createRel = (relType: RelationType, source: string, target: string, sLbl: string, tLbl: string) => {
      const base: Relation = {
        id: uid(), type: relType, sourceId: source, targetId: target,
        label: '', sourceLabel: sLbl, targetLabel: tLbl, version: 0, hash: ''
      };
      generateDeterministicHash({ type: 'relation', data: base }).then(hash => {
        const relation: Relation = { ...base, hash };
        setRelations(prev => [...prev, relation]);
        broadcastDiagramEvent({ action: 'addRelation', payload: { relation } });
        mark();
      });
    };

    const getPK = (node: ClassNode) => node.atributos.find(a => a.visibilidad === 'PK') || node.atributos.find(a => a.nombre.toLowerCase() === 'id') || { tipo: 'int', nombre: 'id' };

    if (type === '1:1' || type === '1:N' || type === '0..1:1' || type === '0..1:N' || type === '0..N:1') {
      const srcPK = getPK(srcNode);
      const newAttr: Atributo = { id: uid(), visibilidad: 'FK', nombre: `id_${srcNode.nombre.toLowerCase()}`, tipo: srcPK.tipo, version: 0 };
      
      addAtributo(tgtNode.id, newAttr);

      let sLbl = '1';
      let tLbl = 'n';
      if (type === '1:1') { sLbl = '1'; tLbl = '1'; }
      else if (type === '1:N') { sLbl = '1'; tLbl = 'n'; }
      else if (type === '0..1:1') { sLbl = '0..1'; tLbl = '1'; }
      else if (type === '0..1:N') { sLbl = '0..1'; tLbl = 'n'; }
      else if (type === '0..N:1') { sLbl = '0..n'; tLbl = '1'; }

      createRel(type, srcNode.id, tgtNode.id, sLbl, tLbl);

    } else if (type === 'N:M' || type === '0..N:M') {
      const srcPK = getPK(srcNode);
      const tgtPK = getPK(tgtNode);
      
      const interId = uid();
      const interNode: ClassNode = {
        id: interId,
        type: 'class',
        estereotipo: 'table',
        x: (srcNode.x + tgtNode.x) / 2,
        y: (srcNode.y + tgtNode.y) / 2 + 100,
        width: 220,
        nombre: `${srcNode.nombre}_${tgtNode.nombre}`,
        color: '#393E46',
        version: 0,
        hash: '',
        metodos: [],
        atributos: [
          { id: uid(), visibilidad: 'PK', nombre: `id_${srcNode.nombre.toLowerCase()}`, tipo: srcPK.tipo, version: 0 },
          { id: uid(), visibilidad: 'PK', nombre: `id_${tgtNode.nombre.toLowerCase()}`, tipo: tgtPK.tipo, version: 0 }
        ]
      };
      
      addNode('class', interNode);
      
      createRel('1:N', srcNode.id, interId, '1', type === '0..N:M' ? '0..n' : 'n');
      createRel('1:N', tgtNode.id, interId, '1', type === '0..N:M' ? '0..m' : 'n');

    } else {
      createRel(type, srcNode.id, tgtNode.id, '', '');
    }

    setConnectingSource(null);
  }, [connectingSource, nodes, addAtributo, addNode, broadcastDiagramEvent, mark]);

  const cancelConnect = useCallback(() => {
    setConnectingSource(null);
    setActiveTool('select');
  }, []);

  // ── Estado del diagrama ──────────────────────────────────────────────────

  const getDiagramState = useCallback((): DiagramState => ({
    nodes,
    relations,
    correcciones,
    version: Date.now(),
  }), [nodes, relations, correcciones]);

  const loadDiagram = useCallback((state: DiagramState) => {
    const loaded = (state.nodes || []).map(n => ({
      ...n,
      type: n.type ?? 'class',
      version: n.version ?? 0,
      hash: n.hash ?? '',
      atributos: (n.atributos || []).map(a => ({ ...a, version: a.version ?? 0 })),
      metodos: (n.metodos || []).map(m => ({ ...m, version: m.version ?? 0 })),
    }));
    const loadedRels = (state.relations || []).map(r => ({
      ...r,
      version: r.version ?? 0,
      hash: r.hash ?? '',
    }));
    setNodes(loaded);
    setRelations(loadedRels);
    setCorrecciones(state.correcciones || {});
    isDirty.current = false;
  }, []);

  // ── Escuchar eventos remotos ─────────────────────────────────────────────

  useEffect(() => {
    const handleRemoteEvent = (e: any) => {
      const { action, payload } = e.detail;
      switch (action) {
        case 'addNode': addNode(payload.node?.type ?? 'class', payload.node, true); break;
        case 'updateNode': updateNode(payload.id, payload.partial, true); break;
        case 'addRelation': setRelations(prev => [...prev, payload.relation]); break;
        case 'updateRelation': updateRelation(payload.id, payload.partial, true); break;
        case 'deleteRelation': deleteRelation(payload.id, true); break;
        case 'deleteNode': deleteNode(payload.id, true); break;
        case 'moveNode': moveNode(payload.id, payload.x, payload.y, true); break;
        case 'addAtributo': addAtributo(payload.nodeId, payload.attr, true); break;
        case 'updateAtributo': updateAtributo(payload.nodeId, payload.attrId, payload.partial, true); break;
        case 'deleteAtributo': deleteAtributo(payload.nodeId, payload.attrId, true); break;
        case 'addMetodo': addMetodo(payload.nodeId, payload.met, true); break;
        case 'updateMetodo': updateMetodo(payload.nodeId, payload.metodId, payload.partial, true); break;
        case 'deleteMetodo': deleteMetodo(payload.nodeId, payload.metodId, true); break;
        case 'addCorreccion': addCorreccion(payload.targetId, payload.texto, payload.autorNombre, payload.corr, true); break;
        case 'resolveCorreccion': resolveCorreccion(payload.targetId, payload.correccionId, payload.resueltoPorNombre, true); break;
      }
    };
    window.addEventListener('remote_diagram_event', handleRemoteEvent);
    return () => window.removeEventListener('remote_diagram_event', handleRemoteEvent);
  }, [addNode, updateNode, deleteNode, moveNode, addAtributo, updateAtributo, deleteAtributo, addMetodo, updateMetodo, deleteMetodo, addCorreccion, resolveCorreccion]);

  return (
    <DiagramContext.Provider value={{
      nodes, relations, correcciones, isOffline, conflicts, selectedIds, connectingSource, activeTool, setSelectedIds, setActiveTool,
      addNode, updateNode, deleteNode, moveNode,
      startConnect, finishConnect, cancelConnect,
      updateRelation, deleteRelation,
      addAtributo, updateAtributo, deleteAtributo,
      addMetodo, updateMetodo, deleteMetodo,
      addCorreccion, resolveCorreccion,
      resolveConflict,
      getDiagramState, loadDiagram, isDirty,
    }}>
      {children}
    </DiagramContext.Provider>
  );
};

export const useDiagram = () => {
  const ctx = useContext(DiagramContext);
  if (!ctx) throw new Error('useDiagram must be inside DiagramProvider');
  return ctx;
};
