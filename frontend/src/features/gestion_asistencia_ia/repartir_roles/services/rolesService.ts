import { apiFetch } from '@/shared/lib/api';
import type {
  RepartirRolesRequest,
  RepartirRolesResponse,
  ColaboradorRolOut,
  AsignarRolManualRequest,
} from '../types';

export async function repartirRolesEquipo(req: RepartirRolesRequest): Promise<RepartirRolesResponse> {
  return apiFetch<RepartirRolesResponse>('/api/ia/roles/repartir', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function obtenerRolesProyecto(proyectoId: number): Promise<ColaboradorRolOut[]> {
  return apiFetch<ColaboradorRolOut[]>(`/api/ia/roles/proyecto/${proyectoId}`);
}

export async function asignarRolManual(req: AsignarRolManualRequest): Promise<ColaboradorRolOut> {
  return apiFetch<ColaboradorRolOut>('/api/ia/roles/asignar', {
    method: 'PUT',
    body: JSON.stringify(req),
  });
}

export const rolesService = {
  repartirRolesEquipo,
  obtenerRolesProyecto,
  asignarRolManual,
};
