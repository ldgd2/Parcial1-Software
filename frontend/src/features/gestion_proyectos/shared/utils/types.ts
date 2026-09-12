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

export interface Notificacion {
  id: string;
  titulo: string;
  mensaje: string;
  tipo: 'exito' | 'error' | 'info' | 'advertencia';
}
