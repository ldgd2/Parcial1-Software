import { TokenService } from '@/shared/lib/TokenService';
import { API_URL } from '@/shared/lib/api';

const getAuthHeaders = (): Record<string, string> => {
  const token = TokenService.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const BASE = `${API_URL}/api/ia/tareas`;

export interface TareaItem {
  id: number;
  proyecto_id: number;
  usuario_id: number;
  tipo: 'diagrama' | 'desarrollo';
  area?: string;
  titulo: string;
  descripcion: string | null;
  completada: boolean;
  orden: number;
}

export interface RepartirTareasRequest {
  proyecto_id: number;
  descripcion_proyecto?: string;
  colaboradores?: Array<{
    usuario_id: number;
    nombre: string;
    rol_ia?: string;
    areas?: string[];
  }>;
  provider?: string;
  api_key?: string;
}

export interface RepartirTareasResponse {
  proyecto_id: number;
  tareas_generadas: number;
  tareas: TareaItem[];
  resumen: string;
}

export async function repartirTareasEquipo(req: RepartirTareasRequest): Promise<RepartirTareasResponse> {
  const res = await fetch(`${BASE}/repartir`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al repartir tareas con IA');
  }
  return res.json();
}

export async function obtenerMisTareas(proyectoId: number): Promise<TareaItem[]> {
  const res = await fetch(`${BASE}/proyecto/${proyectoId}/mis-tareas`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al obtener mis tareas');
  return res.json();
}

export async function obtenerTodasLasTareas(proyectoId: number): Promise<TareaItem[]> {
  const res = await fetch(`${BASE}/proyecto/${proyectoId}/todas`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al obtener todas las tareas del proyecto');
  return res.json();
}

export async function marcarTarea(tareaId: number, completada: boolean): Promise<TareaItem> {
  const res = await fetch(`${BASE}/${tareaId}/completar?completada=${completada}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al actualizar estado de la tarea');
  return res.json();
}

export async function crearTareaManual(req: {
  proyecto_id: number;
  usuario_id: number;
  titulo: string;
  tipo?: string;
  area?: string;
  descripcion?: string;
  orden?: number;
}): Promise<TareaItem> {
  const res = await fetch(`${BASE}/crear`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error('Error al crear tarea manual');
  return res.json();
}

export async function eliminarTarea(tareaId: number): Promise<void> {
  const res = await fetch(`${BASE}/${tareaId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al eliminar tarea');
}

