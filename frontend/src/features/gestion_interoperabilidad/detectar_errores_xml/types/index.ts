export interface ErrorLogicoBD {
  id: string;
  tipo: 'sin_pk' | 'fk_huerfana' | 'tipo_discordante' | 'dependencia_circular' | 'relacion_nm_directa' | 'tabla_aislada' | 'palabra_reservada';
  severidad: 'alta' | 'media' | 'baja';
  tabla: string;
  columna?: string | null;
  descripcion: string;
  solucion_sugerida: string;
}

export interface DetectarErroresResponse {
  total_errores: number;
  es_valido: boolean;
  errores: ErrorLogicoBD[];
  estadisticas: Record<string, number>;
  resumen: string;
}

export interface CorregirErroresResponse {
  resumen: string;
  errores_corregidos: number;
  fixed_nodes: any[];
  fixed_relations: any[];
  fixed_xml?: string | null;
}

