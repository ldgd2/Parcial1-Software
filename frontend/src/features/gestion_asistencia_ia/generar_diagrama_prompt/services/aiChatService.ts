import { apiFetch } from '@/shared/lib/api';
import type { AiProvider } from '../types/chatTypes';

export interface GenerateDiagramResult {
  nodes: any[];
  relations: any[];
  summary: string;
  deletedNodes?: any[];
  deletedRelations?: any[];
  tasks?: Array<{
    titulo: string;
    descripcion?: string;
    tipo?: string;
    rol_sugerido?: string;
  }>;
  provider_used?: string;
  /** Versión del historial creada para esta interacción (para guardar luego el "después") */
  version_id?: number | null;
  /** Tokens reales del pedido (todas las llamadas a la IA que hizo el backend) */
  uso_tokens?: import('../types/chatTypes').UsoTokens | null;
}

export async function callGenerateDiagramAPI(
  prompt: string,
  context: string | null = null,
  provider: AiProvider = 'gemini',
  apiKey: string | null = null,
  proyectoId?: number,
  /** Diagrama ({nodes, relations}) antes de aplicar la respuesta, para el historial de versiones */
  estadoAntes?: { nodes: any[]; relations: any[] } | null,
  autor?: string | null,
  /** Para el botón "Detener": corta la petición (el backend cancela la llamada a la IA) */
  signal?: AbortSignal,
  /** Correcciones del diagrama: la IA las recibe en su memoria */
  correcciones?: Array<{ id: string; target: string; text: string; estado: string }>
): Promise<GenerateDiagramResult> {
  const payload: Record<string, any> = {
    prompt,
    context,
    provider,
    include_tasks: true
  };

  if (estadoAntes) {
    payload.estado_antes = estadoAntes;
  }
  if (autor) {
    payload.autor = autor;
  }
  if (correcciones) {
    payload.correcciones = correcciones;
  }

  if (proyectoId && proyectoId > 0) {
    payload.proyecto_id = proyectoId;
  }

  if (apiKey && apiKey.trim()) {
    payload.api_key = apiKey.trim();
  }

  return await apiFetch<GenerateDiagramResult>('/prompt/generar', {
    method: 'POST',
    body: JSON.stringify(payload),
    signal
  });
}

export async function callTranscribeAudioAPI(
  audioBase64: string,
  mimeType: string = 'audio/webm',
  apiKey: string | null = null
): Promise<string> {
  const payload: Record<string, any> = {
    audio_base64: audioBase64,
    mime_type: mimeType
  };

  if (apiKey && apiKey.trim()) {
    payload.api_key = apiKey.trim();
  }

  const res = await apiFetch<{ text: string }>('/prompt/transcribe-audio', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  return res.text || '';
}

export interface AiPromptConfig {
  default_provider: AiProvider;
  has_gemini: boolean;
  has_openrouter: boolean;
  has_kimi: boolean;
  models: Record<string, string>;
}

export async function fetchAiPromptConfig(): Promise<AiPromptConfig> {
  return await apiFetch<AiPromptConfig>('/prompt/config');
}


