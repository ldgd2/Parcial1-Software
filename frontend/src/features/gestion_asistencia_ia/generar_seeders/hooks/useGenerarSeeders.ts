import { useState, useCallback } from 'react';
import { seedersService } from '../services/seedersService';
import type { GenerarSeedersResponse } from '../types';

interface UseGenerarSeedersProps {
  nodes: any[];
  relations: any[];
  proyectoId?: number;
}

export function useGenerarSeeders({ nodes, relations, proyectoId }: UseGenerarSeedersProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [cantidad, setCantidad] = useState<number>(10);
  const [formato, setFormato] = useState<'sql' | 'java_runner'>('sql');
  const [resultado, setResultado] = useState<GenerarSeedersResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const ejecutarGeneracion = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    setCopied(false);
    try {
      const data = await seedersService.generarSeeders({
        proyecto_id: proyectoId,
        diagram_json: { nodes, relations },
        cantidad_por_tabla: cantidad,
        formato
      });
      setResultado(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error al generar seeders');
    } finally {
      setLoading(false);
    }
  }, [nodes, relations, proyectoId, cantidad, formato]);

  const copiarAlPortapapeles = useCallback(() => {
    if (!resultado) return;
    const texto = formato === 'sql' ? resultado.sql_script : (resultado.java_code || resultado.sql_script);
    navigator.clipboard.writeText(texto).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [resultado, formato]);

  const descargarArchivo = useCallback(() => {
    if (!resultado) return;
    const contenido = formato === 'sql' ? resultado.sql_script : (resultado.java_code || resultado.sql_script);
    const nombreArchivo = formato === 'sql' ? 'V2__seed_data.sql' : 'DatabaseSeedRunner.java';
    const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombreArchivo;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [resultado, formato]);

  return {
    loading,
    cantidad,
    setCantidad,
    formato,
    setFormato,
    resultado,
    errorMessage,
    copied,
    ejecutarGeneracion,
    copiarAlPortapapeles,
    descargarArchivo
  };
}

