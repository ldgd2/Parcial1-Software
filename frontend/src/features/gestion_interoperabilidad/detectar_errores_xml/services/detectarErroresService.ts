import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';
import type { DetectarErroresResponse, CorregirErroresResponse } from '../types';

const API_BASE = `${API_URL}/api/interoperabilidad`;

export const detectarErroresService = {
  async detectarErrores(params: {
    xml_content?: string;
    nodes?: any[];
    relations?: any[];
    proyecto_id?: number;
  }): Promise<DetectarErroresResponse> {
    const token = TokenService.getToken();
    const res = await fetch(`${API_BASE}/detectar-errores`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(params)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al analizar errores lógicos en la base de datos');
    }

    return res.json();
  },

  async corregirErrores(params: {
    xml_content?: string;
    nodes?: any[];
    relations?: any[];
    errores_ids?: string[];
  }): Promise<CorregirErroresResponse> {
    const token = TokenService.getToken();
    const res = await fetch(`${API_BASE}/corregir-errores`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(params)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al corregir errores de lógica');
    }

    return res.json();
  }
};

