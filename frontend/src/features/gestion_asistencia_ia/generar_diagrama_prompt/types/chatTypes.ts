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
  aiStatus?: 'pending' | 'success' | 'error';
  provider?: AiProvider;
  summary?: string;
  tasksCount?: number;
  /** Cambios de la IA pendientes de aprobación (no se aplican solos) */
  propuesta?: PropuestaIA;
}

export interface PropuestaIA {
  versionId: number;
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

