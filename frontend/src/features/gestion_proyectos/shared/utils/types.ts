export interface Colaborador {
  id?: number;
  estado: string;
  username?: string;
}

export interface Proyecto {
  id: number;
  nombre: string;
  descripcion: string;
  propietario_id: number;
  fecha_creacion: string;
  codigo_acceso?: string;
  colaboradores?: Colaborador[];
}

/** CU08 / CU38: miembro aprobado de un proyecto y su permiso */
export interface Miembro {
  usuario_id: number;
  nombre: string;
  email?: string | null;
  rol_proyecto: string;
  permiso: 'edit' | 'view';
  nivel: 'anfitrion' | 'editor' | 'lector';
}

export interface Notificacion {
  id: string;
  titulo: string;
  mensaje: string;
  tipo: 'exito' | 'error' | 'info' | 'advertencia';
}
