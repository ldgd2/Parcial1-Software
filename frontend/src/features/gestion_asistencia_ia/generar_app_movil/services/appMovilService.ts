import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';
import type { AppMovilResponse, RefinarVistaRequest, RefinarVistaResponse } from '../types/appMovilTypes';

const getAuthHeaders = (): Record<string, string> => {
  const token = TokenService.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export async function generarAppMovil(
  proyectoId: number,
  diagramJson: Record<string, any>,
  apiBaseUrl: string = 'http://localhost:8080',
  appName?: string
): Promise<AppMovilResponse> {
  const res = await fetch(`${API_URL}/api/ia/app-movil/generar`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      proyecto_id: proyectoId,
      diagram_json: diagramJson,
      api_base_url: apiBaseUrl,
      app_name: appName,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al generar la aplicación móvil Flutter');
  }

  return res.json();
}

export async function obtenerPreviewAppMovil(proyectoId: number): Promise<AppMovilResponse> {
  const res = await fetch(`${API_URL}/api/ia/app-movil/preview/${proyectoId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener la vista previa de la app móvil');
  }

  return res.json();
}

export async function refinarVistaAppMovil(req: RefinarVistaRequest): Promise<RefinarVistaResponse> {
  const res = await fetch(`${API_URL}/api/ia/app-movil/refinar`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al refinar la vista con IA');
  }

  return res.json();
}

export async function descargarZipAppMovil(proyectoId: number, apiBaseUrl?: string): Promise<void> {
  const token = TokenService.getToken();
  const url = `${API_URL}/api/ia/app-movil/descargar/${proyectoId}?api_base_url=${encodeURIComponent(apiBaseUrl || 'http://10.0.2.2:8080/api')}`;
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al descargar el archivo ZIP del proyecto móvil');
  }

  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  // El backend nombra el ZIP con la app ({app}_flutter.zip); el id queda solo de respaldo
  const disposicion = res.headers.get('Content-Disposition') || '';
  const nombre = disposicion.match(/filename="?([^";]+)"?/i)?.[1];
  a.download = nombre || `app_flutter_${proyectoId}.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(downloadUrl);
}
