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
  memoria_secciones?: MemoriaSecciones | null;
  version_id?: number | null;
}

export interface CompilarContextoResponse {
  proyecto_id: number;
  contexto_compilado_llm: string;
  tokens_estimados: number;
  tokens_ahorrados: number;
  total_eventos_recordados: number;
  correcciones_activas_count: number;
  memoria_secciones?: MemoriaSecciones | null;
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
  estado_antes?: EstadoDiagramaVersion | null;
  estado_despues?: EstadoDiagramaVersion | null;
  autor?: string | null;
}

// ─── Memoria inyectada, por secciones (misma selección que el texto del prompt) ──

export interface MemoriaSecciones {
  dominio: string;
  resumen: string;
  ultimas_acciones: Array<{ ts: number; intent: string; cmd: string; summary: string; delta: string }>;
  correcciones_abiertas: Array<{ target: string; text: string }>;
  total_correcciones_abiertas: number;
  diagrama_dsl: string;
  /** Memoria del proyecto elegida para el pedido (reglas fijas + relevantes) */
  memorias?: Array<{ tipo: string; topic_key: string; titulo: string; que: string; aprendido: string }>;
}

// ─── Versiones del diagrama antes/después de cada interacción de la IA ──────

/** Subconjunto de DiagramState que se guarda por versión. */
export interface EstadoDiagramaVersion {
  nodes: any[];
  relations: any[];
}

export interface VersionResumen {
  id: number;
  ts: number;
  intent: string;
  cmd: string;
  resumen: string;
  delta: string;
  autor?: string | null;
  tiene_antes: boolean;
  tiene_despues: boolean;
  /** Propuestas de la IA: null (no es propuesta) | pendiente | aprobada | rechazada */
  estado_propuesta?: 'pendiente' | 'aprobada' | 'rechazada' | null;
  decidida_por?: string | null;
  decidida_en?: number | null;
}

export interface VersionDetalle extends VersionResumen {
  estado_antes?: EstadoDiagramaVersion | null;
  estado_despues?: EstadoDiagramaVersion | null;
  /** Cambios que propuso la IA (formato de respuesta de /prompt/generar) */
  propuesta?: { nodes: any[]; relations: any[]; deletedNodes?: any[]; deletedRelations?: any[]; summary?: string } | null;
}

export interface VersionesPagina {
  items: VersionResumen[];
  hay_mas: boolean;
}

// ─── Memoria del proyecto (estilo Engram) ───────────────────────────────

export type TipoMemoria = 'decision' | 'restriccion' | 'convencion' | 'correccion' | 'rechazo';

export interface MemoriaItem {
  id: number;
  tipo: TipoMemoria;
  topic_key: string;
  titulo: string;
  que: string;
  por_que: string;
  donde: string;
  aprendido: string;
  origen: 'manual' | 'aprobacion' | 'rechazo' | string;
  autor?: string | null;
  vigente: boolean;
  en_conflicto: boolean;
  reemplaza_id?: number | null;
  version_id?: number | null;
  creada: number;
  actualizada: number;
}
