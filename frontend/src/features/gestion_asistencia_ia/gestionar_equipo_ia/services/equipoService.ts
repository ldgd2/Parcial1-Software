import { getAuthHeaders } from '@/features/gestion_usuarios/shared/utils/auth';

const BASE = '/api/ia/equipo';

export interface HabilidadDesarrollador {
  usuario_id: number;
  nombre: string;
  etiquetas: string[];
}

export interface GenerarEquipoRequest {
  proyecto_id: number;
  descripcion_proyecto: string;
  desarrolladores: HabilidadDesarrollador[];
}

export interface TareaIA {
  id: number;
  proyecto_id: number;
  usuario_id: number;
  tipo: 'diagrama' | 'desarrollo';
  titulo: string;
  descripcion: string | null;
  completada: boolean;
  orden: number;
}

export async function generarTareasEquipo(req: GenerarEquipoRequest): Promise<TareaIA[]> {
  const res = await fetch(`${BASE}/generar`, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error('Error al generar tareas de equipo');
  return res.json();
}

export async function obtenerMisTareas(proyectoId: number): Promise<TareaIA[]> {
  const res = await fetch(`${BASE}/proyecto/${proyectoId}/mis-tareas`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al obtener tareas');
  return res.json();
}

export async function obtenerTodasLasTareas(proyectoId: number): Promise<TareaIA[]> {
  const res = await fetch(`${BASE}/proyecto/${proyectoId}/todas`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al obtener tareas del equipo');
  return res.json();
}

export async function marcarTarea(tareaId: number, completada: boolean): Promise<TareaIA> {
  const res = await fetch(`${BASE}/tarea/${tareaId}/completar?completada=${completada}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al actualizar tarea');
  return res.json();
}

export async function actualizarHabilidades(etiquetas: string[]): Promise<void> {
  const res = await fetch(`${BASE}/habilidades`, {
    method: 'PUT',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ etiquetas }),
  });
  if (!res.ok) throw new Error('Error al actualizar habilidades');
}
