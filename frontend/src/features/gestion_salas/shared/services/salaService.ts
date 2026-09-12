import { apiFetch } from '@/shared/lib/api';
import type { DiagramState } from '@/features/gestion_modelado/shared/types/types';

export const salaService = {
  async cargarLienzo(proyectoId: number) {
    return apiFetch(`/salas/${proyectoId}/lienzo`);
  },

  async guardarLienzo(proyectoId: number, lienzo: DiagramState) {
    return apiFetch(`/salas/${proyectoId}/lienzo`, {
      method: 'PUT',
      body: JSON.stringify({ lienzo }),
    });
  },

  async unirse(codigoAcceso: string) {
    return apiFetch(`/salas/unirse/${codigoAcceso}`);
  },
};
