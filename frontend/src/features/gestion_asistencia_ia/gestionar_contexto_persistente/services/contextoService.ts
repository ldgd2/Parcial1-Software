import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';
import type {
  ContextoIAResponse,
  CompilarContextoResponse,
  RegistrarInteraccionPayload,
  EstadoDiagramaVersion,
  VersionDetalle,
  VersionResumen,
  VersionesPagina
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

// ─── Versiones (antes/después de cada interacción de la IA) ─────────────────

export async function listarVersiones(
  proyectoId: number,
  limite: number = 30,
  antesDeId?: number
): Promise<VersionesPagina> {
  const params = new URLSearchParams({ limite: String(limite) });
  if (antesDeId) params.set('antes_de_id', String(antesDeId));
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}/versiones?${params}`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error(`Error listando versiones: ${response.statusText}`);
  }
  return response.json();
}

export async function obtenerVersion(proyectoId: number, versionId: number): Promise<VersionDetalle> {
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}/versiones/${versionId}`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error(`Error obteniendo la versión: ${response.statusText}`);
  }
  return response.json();
}

export async function guardarVersionDespues(
  proyectoId: number,
  versionId: number,
  estado: EstadoDiagramaVersion
): Promise<VersionResumen> {
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}/versiones/${versionId}/despues`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ estado_despues: estado })
  });
  if (!response.ok) {
    throw new Error(`Error guardando la versión posterior: ${response.statusText}`);
  }
  return response.json();
}

/** Versión de un cambio hecho sin la IA (cambios manuales). No toca la memoria de la IA. */
export async function crearVersion(
  proyectoId: number,
  datos: {
    intent: string;
    cmd: string;
    resumen?: string;
    delta?: string;
    autor?: string | null;
    estado_antes?: EstadoDiagramaVersion | null;
    estado_despues?: EstadoDiagramaVersion | null;
    /** Si se envía, queda como propuesta pendiente de aprobación */
    propuesta?: Record<string, any> | null;
  },
  keepalive = false
): Promise<VersionResumen> {
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}/versiones`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(datos),
    keepalive   // permite terminar el envío al cerrar la pestaña
  });
  if (!response.ok) {
    throw new Error(`Error registrando la versión: ${response.statusText}`);
  }
  return response.json();
}

/** La propuesta ya la decidió otra persona (HTTP 409). */
export class PropuestaYaDecididaError extends Error {
  estado: 'aprobada' | 'rechazada';
  decididaPor: string | null;

  constructor(message: string, estado: 'aprobada' | 'rechazada', decididaPor: string | null) {
    super(message);
    this.estado = estado;
    this.decididaPor = decididaPor;
  }
}

/** Aprueba o rechaza una propuesta de la IA. El backend registra quién decidió. */
export async function decidirPropuesta(
  proyectoId: number,
  versionId: number,
  aceptar: boolean,
  estadoAntes: EstadoDiagramaVersion | null,
  autor: string | null
): Promise<VersionDetalle> {
  const response = await fetch(`${API_URL}/api/ia/contexto/${proyectoId}/versiones/${versionId}/decision`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ aceptar, estado_antes: estadoAntes, autor })
  });
  if (response.status === 409) {
    const data = await response.json().catch(() => ({}));
    const d = data?.detail ?? {};
    throw new PropuestaYaDecididaError(
      d.mensaje || 'La propuesta ya fue decidida.',
      d.estado_propuesta === 'rechazada' ? 'rechazada' : 'aprobada',
      d.decidida_por ?? null
    );
  }
  if (!response.ok) {
    throw new Error(`Error al decidir la propuesta: ${response.statusText}`);
  }
  return response.json();
}
