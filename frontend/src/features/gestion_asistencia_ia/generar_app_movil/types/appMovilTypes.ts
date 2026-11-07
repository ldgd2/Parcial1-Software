export interface AppMovilResponse {
  proyecto_id: number;
  app_name: string;
  archivos_generados: number;
  resumen: string;
  archivos: Record<string, string>;
}

export interface RefinarVistaRequest {
  proyecto_id: number;
  vista_nombre: string;
  codigo_actual: string;
  instrucciones: string;
  api_endpoint?: string;
}

export interface RefinarVistaResponse {
  codigo_refinado: string;
  resumen_cambios: string;
}
