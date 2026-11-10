/**
 * VersionManager – sincronización al volver a tener conexión (CU20).
 *
 * Al perder la red se guarda en cada clase su estado de ese momento (`offlineBase`).
 * Al reconectar se hace un merge de 3 vías por campo (nombre de la clase, nombre/tipo de cada
 * atributo, nombre de cada método) entre: base (al desconectarse), local (mis cambios) y servidor
 * (lo que hicieron los demás, incluido lo que aún no se guardó: el servidor mantiene el estado
 * vivo de la sala).
 *   - Solo cambió el servidor → se aplica el valor del servidor.
 *   - Solo cambié yo → se conserva el mío y se envía a la sala.
 *   - Cambiamos los dos a valores distintos → CONFLICTO: lo resuelve el usuario en el modal.
 *
 * Antes solo se comparaban versiones de atributos/métodos (nunca el nombre de la clase), el
 * resultado no se enviaba a nadie ni se guardaba, y "Aceptar servidor" no hacía nada (CP22/CP23).
 */

import type { ClassNode, Atributo, Metodo, OfflineBase } from '../types/types';

// ─── Tipos del sistema de versiones ─────────────────────────────────────────

export interface ClassVersionSnapshot {
  nodeId: string;
  version: number;
  hash: string;
  atributos: Atributo[];
  metodos: Metodo[];
  nombre?: string;
  type?: string;
  x?: number;
  y?: number;
  width?: number;
  color?: string;
}

export interface ConflictItem {
  nodeId: string;
  nodeName: string;
  field: string;          // "nombre" | "attr:<id>:nombre" | "attr:<id>:tipo" | "met:<id>:nombre"
  localValue: any;
  serverValue: any;
}

export interface SyncResult {
  applied: ClassNode[];       // estado resultante de todas las clases
  conflicts: ConflictItem[];  // decisiones pendientes del usuario
  paraEnviar: string[];       // clases con cambios offline sin conflicto: se envían a la sala
  nuevos: string[];           // clases creadas sin conexión
}

/** Foto de la clase al perder la conexión. */
export function baseOffline(n: ClassNode): OfflineBase {
  return {
    nombre: n.nombre,
    atributos: Object.fromEntries((n.atributos || []).map(a => [a.id, { nombre: a.nombre, tipo: a.tipo }])),
    metodos: Object.fromEntries((n.metodos || []).map(m => [m.id, { nombre: m.nombre }])),
  };
}

type Merge<T> = { valor: T; local: boolean; conflicto: boolean };

/** Merge de 3 vías de un valor. */
function tresVias<T>(base: T, local: T, servidor: T): Merge<T> {
  if (local === servidor) return { valor: local, local: false, conflicto: false };
  if (local === base) return { valor: servidor, local: false, conflicto: false };
  if (servidor === base) return { valor: local, local: true, conflicto: false };
  return { valor: local, local: true, conflicto: true };
}

function limpiar(n: ClassNode): ClassNode {
  return { ...n, offlineBase: undefined, offlineVersion: undefined, isOfflineDirty: false };
}

export function syncOnReconnect(localNodes: ClassNode[], serverSnapshots: ClassVersionSnapshot[]): SyncResult {
  const result: SyncResult = { applied: [], conflicts: [], paraEnviar: [], nuevos: [] };
  const serverMap = new Map(serverSnapshots.map(s => [s.nodeId, s]));

  for (const local of localNodes) {
    const server = serverMap.get(local.id);
    serverMap.delete(local.id);
    const base = local.offlineBase;

    if (!server) {
      // Sin base: la creé sin conexión. Con base: otro la eliminó mientras yo no estaba;
      // se conserva la mía (no se vuelve a enviar).
      result.applied.push(limpiar(local));
      if (!base) result.nuevos.push(local.id);
      continue;
    }

    if (!base) {
      // No estuve desconectado con esta clase: manda el servidor
      result.applied.push(buildMergedNode(local, server));
      continue;
    }

    const { merged, conflicts, cambioLocal } = mergeTresVias(local, server, base);
    result.applied.push(merged);
    result.conflicts.push(...conflicts);
    if (cambioLocal && conflicts.length === 0) result.paraEnviar.push(local.id);
  }

  // Clases que solo existen en el servidor (las crearon otros)
  for (const [, snap] of serverMap) result.applied.push(buildNodeFromSnapshot(snap));

  return result;
}

function mergeTresVias(local: ClassNode, server: ClassVersionSnapshot, base: OfflineBase) {
  const conflicts: ConflictItem[] = [];
  let cambioLocal = false;
  const registrar = (m: Merge<any>, field: string, servidorValor: any) => {
    if (m.local) cambioLocal = true;
    if (m.conflicto) conflicts.push({ nodeId: local.id, nodeName: local.nombre, field, localValue: m.valor, serverValue: servidorValor });
  };

  // Nombre de la clase
  const servidorNombre = server.nombre ?? base.nombre;
  const nombre = tresVias(base.nombre, local.nombre, servidorNombre);
  registrar(nombre, 'nombre', servidorNombre);

  // Atributos
  const attrsServidor = new Map((server.atributos || []).map(a => [a.id, a]));
  const atributos: Atributo[] = [];
  for (const a of local.atributos || []) {
    const s = attrsServidor.get(a.id);
    const b = base.atributos[a.id];
    attrsServidor.delete(a.id);
    if (!s) {
      if (!b) { atributos.push(a); cambioLocal = true; }                 // lo agregué yo
      else if (a.nombre !== b.nombre || a.tipo !== b.tipo) {             // otro lo borró y yo lo edité
        atributos.push(a); cambioLocal = true;
      }                                                                 // otro lo borró: se quita
      continue;
    }
    const bn = b?.nombre ?? s.nombre, bt = b?.tipo ?? s.tipo;
    const mn = tresVias(bn, a.nombre, s.nombre);
    const mt = tresVias(bt, a.tipo, s.tipo);
    registrar(mn, `attr:${a.id}:nombre`, s.nombre);
    registrar(mt, `attr:${a.id}:tipo`, s.tipo);
    atributos.push({ ...a, nombre: mn.valor, tipo: mt.valor });
  }
  for (const [id, s] of attrsServidor) {
    if (base.atributos[id]) cambioLocal = true;   // lo borré yo sin conexión
    else atributos.push(s);                       // lo agregó otro
  }

  // Métodos
  const metsServidor = new Map((server.metodos || []).map(m => [m.id, m]));
  const metodos: Metodo[] = [];
  for (const m of local.metodos || []) {
    const s = metsServidor.get(m.id);
    const b = base.metodos[m.id];
    metsServidor.delete(m.id);
    if (!s) {
      if (!b || m.nombre !== b.nombre) { metodos.push(m); cambioLocal = true; }
      continue;
    }
    const mn = tresVias(b?.nombre ?? s.nombre, m.nombre, s.nombre);
    registrar(mn, `met:${m.id}:nombre`, s.nombre);
    metodos.push({ ...m, nombre: mn.valor });
  }
  for (const [id, s] of metsServidor) {
    if (base.metodos[id]) cambioLocal = true;
    else metodos.push(s);
  }

  const merged: ClassNode = {
    ...limpiar(local),
    nombre: nombre.valor,
    atributos,
    metodos,
    version: Math.max(local.version || 0, server.version || 0),
  };
  return { merged, conflicts, cambioLocal };
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function buildMergedNode(local: ClassNode, server: ClassVersionSnapshot): ClassNode {
  return {
    ...limpiar(local),
    nombre: server.nombre ?? local.nombre,
    version: server.version,
    hash: server.hash,
    atributos: server.atributos,
    metodos: server.metodos,
  };
}

function buildNodeFromSnapshot(snap: ClassVersionSnapshot): ClassNode {
  return {
    id: snap.nodeId,
    type: (snap.type as ClassNode['type']) || 'class',
    x: snap.x ?? 200,
    y: snap.y ?? 200,
    width: snap.width ?? 220,
    nombre: snap.nombre || 'ClaseRemota',
    color: snap.color || '#393E46',
    version: snap.version,
    hash: snap.hash,
    atributos: snap.atributos,
    metodos: snap.metodos,
    isOfflineDirty: false,
  };
}
