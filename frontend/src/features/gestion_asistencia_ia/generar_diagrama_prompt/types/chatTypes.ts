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

