export interface TareaItem {
  id: number;
  proyecto_id: number;
  usuario_id: number;
  tipo: 'diagrama' | 'desarrollo';
  area?: string;
  titulo: string;
  descripcion: string | null;
  completada: boolean;
  orden: number;
}

export interface RepartirTareasRequest {
  proyecto_id: number;
  descripcion_proyecto?: string;
  colaboradores?: Array<{
    usuario_id: number;
    nombre: string;
    rol_ia?: string;
    areas?: string[];
  }>;
  provider?: string;
  api_key?: string;
  /** false: la IA solo propone (las tareas se crean al aprobar) */
  persistir?: boolean;
}

export interface RepartirTareasResponse {
  proyecto_id: number;
  tareas_generadas: number;
  tareas: TareaItem[];
  resumen: string;
}

export interface CrearTareaManualRequest {
  proyecto_id: number;
  usuario_id: number;
  titulo: string;
  tipo?: string;
  area?: string;
  descripcion?: string;
  orden?: number;
}

