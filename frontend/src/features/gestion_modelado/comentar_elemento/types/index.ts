export interface ComentarioElemento {
  id: string;
  proyecto_id: number;
  elemento_id: string;
  elemento_tipo: string;
  autor_id?: number | null;
  autor_nombre: string;
  texto: string;
  estado: 'abierto' | 'resuelto';
  created_at: string;
  updated_at: string;
}

export interface CrearComentarioPayload {
  proyecto_id: number;
  elemento_id: string;
  elemento_tipo: 'node' | 'relation';
  texto: string;
  autor_nombre?: string;
  /** Lo escribe la IA al aplicarse una propuesta: se firma "IA (aprobado por …)" */
  autor_ia?: boolean;
}

export interface ActualizarComentarioPayload {
  texto?: string;
  estado?: 'abierto' | 'resuelto';
}

