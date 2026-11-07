import type { GenerarSeedersRequest, GenerarSeedersResponse } from '../types';

const API_URL = '/api/ia/seeders/generar';

export const seedersService = {
  async generarSeeders(req: GenerarSeedersRequest): Promise<GenerarSeedersResponse> {
    const token = localStorage.getItem('token');
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        proyecto_id: req.proyecto_id,
        diagram_json: req.diagram_json,
        cantidad_por_tabla: req.cantidad_por_tabla || 10,
        formato: req.formato || 'sql'
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al generar seeders de prueba para la base de datos');
    }

    return res.json();
  }
};

