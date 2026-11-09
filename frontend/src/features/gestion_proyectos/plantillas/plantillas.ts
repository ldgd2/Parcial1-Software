/** CU42: plantillas de proyecto (servicio + utilidades). */
import { apiFetch } from '@/shared/lib/api';

export interface PlantillaMeta {
  id: string;            // "base:ventas" | "u:12"
  nombre: string;
  descripcion: string;
  clases: number;
  origen: 'base' | 'usuario';
}

export interface Plantilla extends PlantillaMeta {
  lienzo: { nodes: any[]; relations: any[] };
}

export const listarPlantillas = () => apiFetch<PlantillaMeta[]>('/api/plantillas');
export const obtenerPlantilla = (id: string) => apiFetch<Plantilla>(`/api/plantillas/${encodeURIComponent(id)}`);
export const guardarPlantilla = (nombre: string, descripcion: string, lienzo: { nodes: any[]; relations: any[] }) =>
  apiFetch<PlantillaMeta>('/api/plantillas', { method: 'POST', body: JSON.stringify({ nombre, descripcion, lienzo }) });
export const eliminarPlantilla = (id: string) =>
  apiFetch<void>(`/api/plantillas/${encodeURIComponent(id)}`, { method: 'DELETE' });

/** Evento para abrir "Guardar como plantilla" (lo escucha el modal montado en la sala). */
export const EVENTO_GUARDAR_PLANTILLA = 'abrir_guardar_plantilla';

const nuevoId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `id_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

/**
 * Copia el lienzo de la plantilla con ids NUEVOS: los ids de clases y relaciones son únicos
 * en toda la base, así que dos proyectos creados desde la misma plantilla no pueden compartirlos.
 */
export function prepararLienzo(lienzo: { nodes: any[]; relations: any[] }) {
  const mapa = new Map<string, string>();
  const nodes = (lienzo.nodes || []).map((n: any) => {
    const id = nuevoId();
    mapa.set(String(n.id), id);
    return {
      ...n,
      id,
      version: 0,
      hash: '',
      atributos: (n.atributos || []).map((a: any) => ({ ...a, id: nuevoId(), version: 0 })),
      metodos: (n.metodos || []).map((m: any) => ({ ...m, id: nuevoId(), version: 0 })),
    };
  });
  const relations = (lienzo.relations || [])
    .filter((r: any) => mapa.has(String(r.sourceId)) && mapa.has(String(r.targetId)))
    .map((r: any) => ({
      ...r,
      id: nuevoId(),
      sourceId: mapa.get(String(r.sourceId)),
      targetId: mapa.get(String(r.targetId)),
      version: 0,
      hash: '',
    }));
  return { nodes, relations, correcciones: {}, version: Date.now() };
}
