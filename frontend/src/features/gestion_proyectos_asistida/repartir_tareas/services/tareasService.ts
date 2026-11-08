import { apiFetch } from '@/shared/lib/api';
import type {
  RepartirTareasRequest,
  RepartirTareasResponse,
  TareaItem,
  CrearTareaManualRequest,
} from '../types';

export async function repartirTareasEquipo(req: RepartirTareasRequest): Promise<RepartirTareasResponse> {
  return apiFetch<RepartirTareasResponse>('/api/ia/tareas/repartir', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function obtenerMisTareas(proyectoId: number): Promise<TareaItem[]> {
  return apiFetch<TareaItem[]>(`/api/ia/tareas/proyecto/${proyectoId}/mis-tareas`);
}

export async function obtenerTodasLasTareas(proyectoId: number): Promise<TareaItem[]> {
  return apiFetch<TareaItem[]>(`/api/ia/tareas/proyecto/${proyectoId}/todas`);
}

export async function marcarTarea(tareaId: number, completada: boolean): Promise<TareaItem> {
  return apiFetch<TareaItem>(`/api/ia/tareas/${tareaId}/completar?completada=${completada}`, {
    method: 'PATCH',
  });
}

export async function crearTareaManual(req: CrearTareaManualRequest): Promise<TareaItem> {
  return apiFetch<TareaItem>('/api/ia/tareas/crear', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function eliminarTarea(tareaId: number): Promise<{ ok: boolean; eliminada: number }> {
  return apiFetch<{ ok: boolean; eliminada: number }>(`/api/ia/tareas/${tareaId}`, {
    method: 'DELETE',
  });
}

export const tareasService = {
  repartirTareasEquipo,
  obtenerMisTareas,
  obtenerTodasLasTareas,
  marcarTarea,
  crearTareaManual,
  eliminarTarea,
};
