import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';
import type {
  ComentarioElemento,
  CrearComentarioPayload,
  ActualizarComentarioPayload
} from '../types';

function getAuthHeaders(): HeadersInit {
  const token = TokenService.getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

export async function listarComentariosElemento(
  proyectoId: number,
  elementoId: string
): Promise<ComentarioElemento[]> {
  const response = await fetch(
    `${API_URL}/api/modelado/comentarios/elemento/${elementoId}?proyecto_id=${proyectoId}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  );
  if (!response.ok) {
    throw new Error(`Error al listar comentarios del elemento: ${response.statusText}`);
  }
  return response.json();
}

export async function listarTodosComentariosProyecto(
  proyectoId: number
): Promise<ComentarioElemento[]> {
  const response = await fetch(
    `${API_URL}/api/modelado/comentarios/proyecto/${proyectoId}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  );
  if (!response.ok) {
    throw new Error(`Error al listar comentarios del proyecto: ${response.statusText}`);
  }
  return response.json();
}

export async function crearComentarioElemento(
  payload: CrearComentarioPayload
): Promise<ComentarioElemento> {
  const response = await fetch(`${API_URL}/api/modelado/comentarios`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Error al crear comentario: ${response.statusText}`);
  }
  return response.json();
}

export async function actualizarComentarioElemento(
  comentarioId: string,
  payload: ActualizarComentarioPayload
): Promise<ComentarioElemento> {
  const response = await fetch(`${API_URL}/api/modelado/comentarios/${comentarioId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Error al actualizar comentario: ${response.statusText}`);
  }
  return response.json();
}

export async function eliminarComentarioElemento(
  comentarioId: string
): Promise<{ ok: boolean; message: string }> {
  const response = await fetch(`${API_URL}/api/modelado/comentarios/${comentarioId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error(`Error al eliminar comentario: ${response.statusText}`);
  }
  return response.json();
}

