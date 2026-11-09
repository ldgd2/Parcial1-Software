export type AiProvider = 'gemini' | 'kimi' | 'openrouter';

export interface QuotedMessage {
  id: string;
  senderName: string;
  text: string;
  senderColor?: string;
}

export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  senderColor: string;
  text: string;
  timestamp: number;
  replyTo?: QuotedMessage;
  isAi?: boolean;
  aiStatus?: 'pending' | 'success' | 'error' | 'cancelled';
  provider?: AiProvider;
  summary?: string;
  tasksCount?: number;
  /** Cambios de la IA pendientes de aprobación (no se aplican solos) */
  propuesta?: PropuestaIA;
  /** Sugerencias de mejora sobre el diagrama (CU33); cada una se puede pedir a @diag */
  sugerencias?: SugerenciaIA[];
  /** Archivo generado (p. ej. /documentar): cualquiera de la sala lo puede descargar */
  archivo?: { nombre: string; contenido: string };
  /** Pedido nacido de "Solucionar con IA": la corrección que resuelve */
  correccion?: { nodoId: string; id: string; clase: string };
  /** Tokens reales que gastó este pedido (lo informa el backend) */
  usoTokens?: UsoTokens;
}

export interface UsoTokens {
  llamadas: number;
  entrada: number;
  salida: number;
  proveedores: string[];
  /** true si el proveedor no informó tokens y se estimaron por caracteres */
  estimado: boolean;
}

export interface SugerenciaIA {
  /** tipo:clase:atributo — evita repetir la misma sugerencia */
  clave: string;
  severidad: string;
  texto: string;
  detalle: string;
  /** Pedido que se envía a @diag al pulsar "Aplicar" */
  pedido: string;
}

export interface PropuestaIA {
  versionId: number;
  /** Corrección que se marca resuelta al aprobar */
  correccion?: { nodoId: string; id: string; clase: string };
  /** Qué se aplica al aprobar (por defecto, cambios del diagrama) */
  tipo?: 'diagrama' | 'roles' | 'tareas';
  /** Resumen legible para roles / tareas ("Ana → Backend Lead (3 clases)") */
  lineas?: string[];
  /** Tareas incluidas en la propuesta */
  tareas?: number;
  estado: 'pendiente' | 'aprobada' | 'rechazada';
  solicitadaPor: string;
  decididaPor?: string | null;
  decididaEn?: number;
  agregadas: string[];
  modificadas: string[];
  eliminadas: string[];
  relaciones: number;
  /** Datos para aplicar igual que antes (posición y modo refactor) */
  offset: number;
  refactor: boolean;
}

export interface RoomUserMention {
  id: string;
  name: string;
  color: string;
  isAi?: boolean;
}

export interface ParallelAiTask {
  taskId: string;
  promptMessageId: string;
  prompt: string;
  provider: AiProvider;
  status: 'pending' | 'success' | 'error';
  startTime: number;
}

