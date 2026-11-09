import type { EstadoDiagramaVersion } from '../types';

export type EstadoCambio = 'agregado' | 'eliminado' | 'modificado' | 'igual';

export interface CambiosMiembros {
  agregados: string[];
  eliminados: string[];
  modificados: Array<{ antes: string; despues: string }>;
}

export interface CambioNodo {
  id: string;
  nombre: string;
  estado: EstadoCambio;
  renombradoDe?: string;
  atributos: CambiosMiembros;
  metodos: CambiosMiembros;
}

export interface ComparacionVersiones {
  nodos: CambioNodo[];
  /** estado de cada nodo por id, tanto del lado "antes" como del "después" */
  estadoPorId: Record<string, EstadoCambio>;
  /** firma de cada miembro cambiado por id de nodo, para resaltarlo en el preview */
  miembrosPorNodo: Record<string, { agregados: Set<string>; eliminados: Set<string>; modificados: Set<string> }>;
  relacionesAgregadas: string[];
  relacionesEliminadas: string[];
  estadoRelacionPorId: Record<string, EstadoCambio>;
  sinCambios: boolean;
}

const VACIO: EstadoDiagramaVersion = { nodes: [], relations: [] };

export const firmaAtributo = (a: any): string =>
  `${a?.visibilidad ?? '+'} ${a?.nombre ?? ''}: ${a?.tipo ?? ''}`.trim();

export const firmaMetodo = (m: any): string =>
  `${m?.visibilidad ?? '+'} ${m?.nombre ?? ''}(${m?.parametros ?? ''}): ${m?.retorno ?? 'void'}`.trim();

const norm = (s: unknown) => String(s ?? '').trim().toLowerCase();

/** Empareja elementos por id y, si no hay coincidencia, por nombre. */
function emparejar<T>(antes: T[], despues: T[], id: (x: T) => string, nombre: (x: T) => string) {
  const pares: Array<[T, T]> = [];
  const soloAntes: T[] = [];
  const restantes = new Map<string, T>(despues.map(d => [id(d), d]));
  const porNombre = new Map<string, T>();
  despues.forEach(d => { if (!porNombre.has(norm(nombre(d)))) porNombre.set(norm(nombre(d)), d); });

  antes.forEach(a => {
    let d = restantes.get(id(a));
    if (!d) {
      const cand = porNombre.get(norm(nombre(a)));
      if (cand && restantes.has(id(cand))) d = cand;
    }
    if (d) {
      pares.push([a, d]);
      restantes.delete(id(d));
    } else {
      soloAntes.push(a);
    }
  });
  return { pares, soloAntes, soloDespues: [...restantes.values()] };
}

function compararMiembros(antes: any[] = [], despues: any[] = [], firma: (x: any) => string): CambiosMiembros {
  const { pares, soloAntes, soloDespues } = emparejar(antes, despues, x => String(x?.id ?? firma(x)), x => x?.nombre);
  return {
    agregados: soloDespues.map(firma),
    eliminados: soloAntes.map(firma),
    modificados: pares
      .filter(([a, d]) => firma(a) !== firma(d))
      .map(([a, d]) => ({ antes: firma(a), despues: firma(d) })),
  };
}

const hayCambios = (c: CambiosMiembros) => c.agregados.length + c.eliminados.length + c.modificados.length > 0;

const claveRelacion = (r: any, nombres: Map<string, string>) =>
  `${nombres.get(r.sourceId) ?? r.sourceId}→${nombres.get(r.targetId) ?? r.targetId}:${r.type ?? 'association'}`;

export function compararVersiones(
  antesEstado?: EstadoDiagramaVersion | null,
  despuesEstado?: EstadoDiagramaVersion | null
): ComparacionVersiones {
  const antes = antesEstado ?? VACIO;
  const despues = despuesEstado ?? VACIO;

  const { pares, soloAntes, soloDespues } = emparejar(
    antes.nodes || [], despues.nodes || [], (n: any) => String(n.id), (n: any) => n.nombre
  );

  const nodos: CambioNodo[] = [];
  const estadoPorId: Record<string, EstadoCambio> = {};
  const miembrosPorNodo: ComparacionVersiones['miembrosPorNodo'] = {};

  const registrarMiembros = (id: string, atr: CambiosMiembros, met: CambiosMiembros) => {
    miembrosPorNodo[id] = {
      agregados: new Set([...atr.agregados, ...met.agregados]),
      eliminados: new Set([...atr.eliminados, ...met.eliminados]),
      modificados: new Set([...atr.modificados.map(m => m.despues), ...met.modificados.map(m => m.despues)]),
    };
  };

  pares.forEach(([a, d]) => {
    const atributos = compararMiembros(a.atributos, d.atributos, firmaAtributo);
    const metodos = compararMiembros(a.metodos, d.metodos, firmaMetodo);
    const renombrado = norm(a.nombre) !== norm(d.nombre);
    const tipoCambiado = (a.type ?? 'class') !== (d.type ?? 'class');
    const estado: EstadoCambio =
      renombrado || tipoCambiado || hayCambios(atributos) || hayCambios(metodos) ? 'modificado' : 'igual';
    estadoPorId[String(a.id)] = estado;
    estadoPorId[String(d.id)] = estado;
    registrarMiembros(String(d.id), atributos, metodos);
    // del lado "antes", los eliminados del miembro son los que se resaltan
    miembrosPorNodo[String(a.id)] = miembrosPorNodo[String(a.id)] ?? {
      agregados: new Set(), eliminados: new Set([...atributos.eliminados, ...metodos.eliminados]),
      modificados: new Set([...atributos.modificados.map(m => m.antes), ...metodos.modificados.map(m => m.antes)]),
    };
    if (estado !== 'igual') {
      nodos.push({
        id: String(d.id), nombre: d.nombre, estado,
        renombradoDe: renombrado ? a.nombre : undefined, atributos, metodos,
      });
    }
  });

  soloDespues.forEach((d: any) => {
    estadoPorId[String(d.id)] = 'agregado';
    const atributos = compararMiembros([], d.atributos, firmaAtributo);
    const metodos = compararMiembros([], d.metodos, firmaMetodo);
    nodos.push({ id: String(d.id), nombre: d.nombre, estado: 'agregado', atributos, metodos });
  });

  soloAntes.forEach((a: any) => {
    estadoPorId[String(a.id)] = 'eliminado';
    nodos.push({
      id: String(a.id), nombre: a.nombre, estado: 'eliminado',
      atributos: { agregados: [], eliminados: (a.atributos || []).map(firmaAtributo), modificados: [] },
      metodos: { agregados: [], eliminados: (a.metodos || []).map(firmaMetodo), modificados: [] },
    });
  });

  // Relaciones: se comparan por (origen → destino : tipo) usando nombres de clase
  const nombres = new Map<string, string>();
  [...(antes.nodes || []), ...(despues.nodes || [])].forEach((n: any) => nombres.set(String(n.id), n.nombre));
  const clavesAntes = new Map((antes.relations || []).map((r: any) => [claveRelacion(r, nombres), r]));
  const clavesDespues = new Map((despues.relations || []).map((r: any) => [claveRelacion(r, nombres), r]));
  const estadoRelacionPorId: Record<string, EstadoCambio> = {};
  const relacionesAgregadas: string[] = [];
  const relacionesEliminadas: string[] = [];
  clavesDespues.forEach((r: any, k) => {
    const nueva = !clavesAntes.has(k);
    estadoRelacionPorId[String(r.id)] = nueva ? 'agregado' : 'igual';
    if (nueva) relacionesAgregadas.push(k);
  });
  clavesAntes.forEach((r: any, k) => {
    const borrada = !clavesDespues.has(k);
    estadoRelacionPorId[String(r.id)] = borrada ? 'eliminado' : (estadoRelacionPorId[String(r.id)] ?? 'igual');
    if (borrada) relacionesEliminadas.push(k);
  });

  const orden: Record<EstadoCambio, number> = { agregado: 0, modificado: 1, eliminado: 2, igual: 3 };
  nodos.sort((x, y) => orden[x.estado] - orden[y.estado] || x.nombre.localeCompare(y.nombre));

  return {
    nodos,
    estadoPorId,
    miembrosPorNodo,
    relacionesAgregadas,
    relacionesEliminadas,
    estadoRelacionPorId,
    sinCambios: nodos.length === 0 && relacionesAgregadas.length === 0 && relacionesEliminadas.length === 0,
  };
}

// ─── Restaurar ───────────────────────────────────────────────────────────────

export interface AccionesDiagrama {
  addNode: (type?: any, node?: any, isRemote?: boolean) => void;
  updateNode: (id: string, partial: any, isRemote?: boolean) => void;
  deleteNode: (id: string, isRemote?: boolean) => void;
  addRelation: (relation: any, isRemote?: boolean) => void;
  updateRelation: (id: string, partial: any, isRemote?: boolean) => void;
  deleteRelation: (id: string, isRemote?: boolean) => void;
}

const CAMPOS_NODO = ['type', 'nombre', 'color', 'x', 'y', 'width', 'height', 'atributos', 'metodos',
  'responsable', 'responsabilidades'] as const;
const CAMPOS_RELACION = ['type', 'sourceId', 'targetId', 'label', 'sourceLabel', 'targetLabel',
  'waypoints', 'sourceEndpoint', 'targetEndpoint'] as const;

const igual = (a: unknown, b: unknown) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);

/**
 * Lleva la pizarra actual a `objetivo` usando las acciones normales del diagrama
 * (que se transmiten a toda la sala), en vez de `loadDiagram`, que solo cambia
 * la pizarra local. Devuelve cuántas operaciones aplicó.
 */
export function restaurarVersion(
  actual: EstadoDiagramaVersion,
  objetivo: EstadoDiagramaVersion,
  acciones: AccionesDiagrama
): number {
  let ops = 0;
  const nodosObjetivo = new Map((objetivo.nodes || []).map((n: any) => [String(n.id), n]));
  const nodosActuales = new Map((actual.nodes || []).map((n: any) => [String(n.id), n]));
  const relObjetivo = new Map((objetivo.relations || []).map((r: any) => [String(r.id), r]));
  const relActuales = new Map((actual.relations || []).map((r: any) => [String(r.id), r]));

  // 1. Quitar relaciones y clases que no existían en esa versión
  relActuales.forEach((_r, id) => { if (!relObjetivo.has(id)) { acciones.deleteRelation(id); ops++; } });
  nodosActuales.forEach((_n, id) => { if (!nodosObjetivo.has(id)) { acciones.deleteNode(id); ops++; } });

  // 2. Volver a crear o actualizar las clases
  nodosObjetivo.forEach((n: any, id) => {
    const existente = nodosActuales.get(id);
    if (!existente) {
      acciones.addNode(n.type ?? 'class', n);
      ops++;
      return;
    }
    const parcial: Record<string, unknown> = {};
    CAMPOS_NODO.forEach(c => { if (!igual(existente[c], n[c])) parcial[c] = n[c]; });
    if (Object.keys(parcial).length) { acciones.updateNode(id, parcial); ops++; }
  });

  // 3. Relaciones (después de las clases, para que existan sus extremos)
  relObjetivo.forEach((r: any, id) => {
    const existente = relActuales.get(id);
    if (!existente) {
      acciones.addRelation(r);
      ops++;
      return;
    }
    const parcial: Record<string, unknown> = {};
    CAMPOS_RELACION.forEach(c => { if (!igual(existente[c], r[c])) parcial[c] = r[c]; });
    if (Object.keys(parcial).length) { acciones.updateRelation(id, parcial); ops++; }
  });

  return ops;
}
