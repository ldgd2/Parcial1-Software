export interface EventoEpisodico {
  ts: number;
  intent: string;
  cmd: string;
  delta: string;
  summary: string;
}

export interface CorreccionItem {
  id: string;
  target: string;
  text: string;
  estado: 'abierta' | 'resuelta';
}

export interface ContextoIAResponse {
  id: number;
  proyecto_id: number;
  dominio: string;
  resumen_acumulado: string;
  historial_comprimido: EventoEpisodico[];
  correcciones: CorreccionItem[];
  snapshot_dsl: string;
  tokens_ahorrados_estimados: number;
  version: number;
  contexto_compilado_llm: string;
  fecha_actualizacion?: string;
}

export interface CompilarContextoResponse {
  proyecto_id: number;
  contexto_compilado_llm: string;
  tokens_estimados: number;
  tokens_ahorrados: number;
  total_eventos_recordados: number;
  correcciones_activas_count: number;
}

export interface RegistrarInteraccionPayload {
  proyecto_id: number;
  user_prompt: string;
  ai_summary?: string;
  intent?: string;
  added_nodes?: string[];
  updated_nodes?: string[];
  deleted_nodes?: string[];
  diagram_dsl?: string;
  correcciones?: CorreccionItem[];
}

