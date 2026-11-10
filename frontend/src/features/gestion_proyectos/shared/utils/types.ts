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

/** CU08: miembro aprobado de un proyecto y su permiso */
export interface Miembro {
  usuario_id: number;
  nombre: string;
  email?: string | null;
  rol_proyecto: string;
  estado: string;
  permiso: 'anfitrion' | 'editor' | 'lector';
}

export interface Notificacion {
  id: string;
  titulo: string;
  mensaje: string;
  tipo: 'exito' | 'error' | 'info' | 'advertencia';
}
