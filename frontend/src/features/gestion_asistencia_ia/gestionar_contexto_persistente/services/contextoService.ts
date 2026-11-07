import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';
import type {
  ContextoIAResponse,
  CompilarContextoResponse,
  RegistrarInteraccionPayload
} from '../types';

function getAuthHeaders(): HeadersInit {
  const token = TokenService.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

export async function obtenerContextoProyecto(proyectoId: number): Promise<ContextoIAResponse> {
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error(`Error obteniendo contexto del proyecto: ${response.statusText}`);
  }
  return response.json();
}

export async function registrarInteraccion(payload: RegistrarInteraccionPayload): Promise<ContextoIAResponse> {
  const response = await fetch(`${API_URL}/api/ia/contexto/interaccion`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Error registrando interacción: ${response.statusText}`);
  }
  return response.json();
}

export async function guardarSnapshotDiagrama(
  proyectoId: number,
  diagramDsl: string,
  dominio?: string,
  resumenAcumulado?: string
): Promise<ContextoIAResponse> {
  const response = await fetch(`${API_URL}/api/ia/contexto/snapshot`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      proyecto_id: proyectoId,
      diagram_dsl: diagramDsl,
      dominio,
      resumen_acumulado: resumenAcumulado
    })
  });
  if (!response.ok) {
    throw new Error(`Error guardando snapshot del diagrama: ${response.statusText}`);
  }
  return response.json();
}

export async function compilarContextoLlm(proyectoId: number): Promise<CompilarContextoResponse> {
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}/compilado`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error(`Error compilando contexto para LLM: ${response.statusText}`);
  }
  return response.json();
}

export async function limpiarMemoriaContexto(
  proyectoId: number,
  conservarDominio: boolean = true
): Promise<ContextoIAResponse> {
  const response = await fetch(`${API_URL}/api/ia/contexto/limpiar`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      proyecto_id: proyectoId,
      conservar_dominio: conservarDominio
    })
  });
  if (!response.ok) {
    throw new Error(`Error limpiando memoria del contexto: ${response.statusText}`);
  }
  return response.json();
}

