export interface ColaboradorRolInput {
  usuario_id: number;
  nombre: string;
  etiquetas?: string[];
}

export interface RepartirRolesRequest {
  proyecto_id: number;
  colaboradores?: ColaboradorRolInput[];
  instrucciones?: string;
  provider?: string;
  api_key?: string;
}

export interface ColaboradorRolOut {
  usuario_id: number;
  nombre: string;
  rol_ia?: string;
  areas: string[];
  responsabilidades: string[];
  clases_asignadas: string[];
}

export interface RepartirRolesResponse {
  proyecto_id: number;
  resumen: string;
  roles: ColaboradorRolOut[];
}

export interface AsignarRolManualRequest {
  proyecto_id: number;
  usuario_id: number;
  rol_ia: string;
  areas: string[];
  responsabilidades?: string[];
}

