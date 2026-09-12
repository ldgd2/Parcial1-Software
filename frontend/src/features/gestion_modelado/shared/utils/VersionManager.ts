/**
 * VersionManager – Lógica de versionado tipo Git.
 *
 * Reglas:
 *  - Versión 0 → recién creado.
 *  - Cada edición semántica (nombre, tipo, atributo, método) sube la versión.
 *  - Posición (x, y) NO sube la versión.
 *  - Al entrar en offline se congela la versión en `offlineVersion`.
 *  - Al volver online: se hace el diff y se aplican los cambios del servidor que no tenías.
 */

import type { ClassNode, Atributo, Metodo } from '../types/types';

// ─── Tipos del sistema de versiones ─────────────────────────────────────────

export interface ClassVersionSnapshot {
  nodeId: string;
  version: number;
  hash: string;
  atributos: Atributo[];
  metodos: Metodo[];
}

export interface ConflictItem {
  nodeId: string;
  nodeName: string;
  field: string;          // "nombre", "color", attrId, metId
  localValue: any;
  serverValue: any;
}

export interface SyncResult {
  applied: ClassNode[];         // Clases que se actualizaron automáticamente
  conflicts: ConflictItem[];    // Conflictos que el usuario debe resolver
}

// ─── Algoritmo principal de sincronización ──────────────────────────────────

/**
 * syncOnReconnect
 * Se llama cuando el cliente vuelve a estar online.
 *
 * Recibe las snapshots del servidor y las clases locales actuales.
 * Aplica el algoritmo:
 *   1. Si hash local === hash servidor → sin cambios, ignorar.
 *   2. Si solo el servidor tiene cambios nuevos (yo estaba offline sin editar) → aplicar.
 *   3. Si ambos cambiaron → hacer diff field-by-field y detectar conflictos.
 */
export function syncOnReconnect(
  localNodes: ClassNode[],
  serverSnapshots: ClassVersionSnapshot[]
): SyncResult {
  const result: SyncResult = { applied: [], conflicts: [] };
  const serverMap = new Map<string, ClassVersionSnapshot>(
    serverSnapshots.map(s => [s.nodeId, s])
  );

  for (const local of localNodes) {
    const server = serverMap.get(local.id);

    if (!server) {
      // La clase solo existe en local → es nueva offline, aplicar tal cual
      result.applied.push(local);
      continue;
    }

    // Mismo hash semántico → nadie cambió nada
    if (local.hash === server.hash) {
      result.applied.push(local);
      serverMap.delete(local.id);
      continue;
    }

    // Si la clase NO tenía cambios offline (offlineVersion === undefined o !isOfflineDirty)
    // → el servidor manda los cambios, aplicar todos sin preguntar
    if (!local.isOfflineDirty) {
      const merged = buildMergedNode(local, server);
      result.applied.push(merged);
      serverMap.delete(local.id);
      continue;
    }

    // Ambos cambiaron → diff granular
    const { merged, conflicts } = diffAndMerge(local, server);
    result.applied.push(merged);
    result.conflicts.push(...conflicts);
    serverMap.delete(local.id);
  }

  // Clases que existen en el servidor pero no en local → agregar
  for (const [, snap] of serverMap) {
    result.applied.push(buildNodeFromSnapshot(snap));
  }

  return result;
}

// ─── Diff granular ──────────────────────────────────────────────────────────

function diffAndMerge(local: ClassNode, server: ClassVersionSnapshot): { merged: ClassNode; conflicts: ConflictItem[] } {
  const conflicts: ConflictItem[] = [];
  let merged = { ...local, isOfflineDirty: false };

  // Diff de atributos: vServer - vLocal (los que el servidor tiene y yo no)
  const localAttrIds = new Set(local.atributos.map(a => a.id));
  const serverAttrIds = new Set(server.atributos.map(a => a.id));

  // Nuevos atributos del servidor → agregarlos sin conflicto
  const newServerAttrs = server.atributos.filter(a => !localAttrIds.has(a.id));
  merged.atributos = [...local.atributos, ...newServerAttrs];

  // Atributos que ambos tienen → comparar versión por versión
  for (const localAttr of local.atributos) {
    if (!serverAttrIds.has(localAttr.id)) continue; // yo lo agregué offline
    const serverAttr = server.atributos.find(a => a.id === localAttr.id)!;

    if (localAttr.version !== serverAttr.version) {
      // Misma versión base pero valores distintos → CONFLICTO en cada campo
      if (localAttr.nombre !== serverAttr.nombre) {
        conflicts.push({
          nodeId: local.id,
          nodeName: local.nombre,
          field: `attr:${localAttr.id}:nombre`,
          localValue: localAttr.nombre,
          serverValue: serverAttr.nombre,
        });
      }
      if (localAttr.tipo !== serverAttr.tipo) {
        conflicts.push({
          nodeId: local.id,
          nodeName: local.nombre,
          field: `attr:${localAttr.id}:tipo`,
          localValue: localAttr.tipo,
          serverValue: serverAttr.tipo,
        });
      }
    }
  }

  // Diff de métodos (igual que atributos)
  const localMetIds = new Set(local.metodos.map(m => m.id));
  const serverMetIds = new Set(server.metodos.map(m => m.id));

  const newServerMets = server.metodos.filter(m => !localMetIds.has(m.id));
  merged.metodos = [...local.metodos, ...newServerMets];

  for (const localMet of local.metodos) {
    if (!serverMetIds.has(localMet.id)) continue;
    const serverMet = server.metodos.find(m => m.id === localMet.id)!;

    if (localMet.version !== serverMet.version) {
      if (localMet.nombre !== serverMet.nombre) {
        conflicts.push({
          nodeId: local.id,
          nodeName: local.nombre,
          field: `met:${localMet.id}:nombre`,
          localValue: localMet.nombre,
          serverValue: serverMet.nombre,
        });
      }
    }
  }

  return { merged, conflicts };
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function buildMergedNode(local: ClassNode, server: ClassVersionSnapshot): ClassNode {
  return {
    ...local,
    version: server.version,
    hash: server.hash,
    atributos: server.atributos,
    metodos: server.metodos,
    isOfflineDirty: false,
    offlineVersion: undefined,
  };
}

function buildNodeFromSnapshot(snap: ClassVersionSnapshot): ClassNode {
  return {
    id: snap.nodeId,
    type: 'class',
    x: 200,
    y: 200,
    width: 220,
    nombre: 'ClaseRemota',
    color: '#393E46',
    version: snap.version,
    hash: snap.hash,
    atributos: snap.atributos,
    metodos: snap.metodos,
    isOfflineDirty: false,
  };
}
