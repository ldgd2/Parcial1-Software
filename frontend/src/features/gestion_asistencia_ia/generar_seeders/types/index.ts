export interface GenerarSeedersRequest {
  proyecto_id?: number;
  diagram_json?: {
    nodes: any[];
    relations: any[];
  };
  cantidad_por_tabla?: number;
  formato?: 'sql' | 'java_runner' | 'json';
}

export interface GenerarSeedersResponse {
  resumen: string;
  total_tablas: number;
  total_registros: number;
  orden_insercion: string[];
  registros_por_tabla: Record<string, number>;
  sql_script: string;
  java_code?: string | null;
}

