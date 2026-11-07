import { apiFetch } from '@/shared/lib/api';
import type { GenerarSeedersRequest, GenerarSeedersResponse } from '../types';

export const seedersService = {
  async generarSeeders(req: GenerarSeedersRequest): Promise<GenerarSeedersResponse> {
    return apiFetch<GenerarSeedersResponse>('/api/ia/seeders/generar', {
      method: 'POST',
      body: JSON.stringify({
        proyecto_id: req.proyecto_id,
        diagram_json: req.diagram_json,
        cantidad_por_tabla: req.cantidad_por_tabla || 10,
        formato: req.formato || 'sql'
      })
    });
  }
};
