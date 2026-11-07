import { TokenService } from '@/shared/lib/TokenService';
import { API_URL } from '@/shared/lib/api';

const getAuthHeaders = (): Record<string, string> => {
  const token = TokenService.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const BASE = `${API_URL}/api/ia/roles`;

export interface ColaboradorRolInput {
  usuario_id: number;
  nombre: string;
  etiquetas?: string[];
}

export interface RepartirRolesRequest {
  proyecto_id: number;
  colaboradores?: ColaboradorRolInput[];
  instrucciones?: string;
  provider?: string;
  api_key?: string;
}

export interface ColaboradorRolOut {
  usuario_id: number;
  nombre: string;
  rol_ia?: string;
  areas: string[];
  responsabilidades: string[];
  clases_asignadas: string[];
}

export interface RepartirRolesResponse {
  proyecto_id: number;
  resumen: string;
  roles: ColaboradorRolOut[];
}

export interface AsignarRolManualRequest {
  proyecto_id: number;
  usuario_id: number;
  rol_ia: string;
  areas: string[];
  responsabilidades?: string[];
}

export async function repartirRolesEquipo(req: RepartirRolesRequest): Promise<RepartirRolesResponse> {
  const res = await fetch(`${BASE}/repartir`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al repartir roles con IA');
  }
  return res.json();
}

export async function obtenerRolesProyecto(proyectoId: number): Promise<ColaboradorRolOut[]> {
  const res = await fetch(`${BASE}/proyecto/${proyectoId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Error al obtener roles del proyecto');
  return res.json();
}

export async function asignarRolManual(req: AsignarRolManualRequest): Promise<ColaboradorRolOut> {
  const res = await fetch(`${BASE}/asignar`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error('Error al asignar rol manualmente');
  return res.json();
}

