import { useState, useCallback } from 'react';
import {
  generarAppMovil,
  obtenerPreviewAppMovil,
  refinarVistaAppMovil,
} from '../services/appMovilService';
import type { AppMovilResponse } from '../types/appMovilTypes';

export function useAppMovil(proyectoId: number) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appData, setAppData] = useState<AppMovilResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [refining, setRefining] = useState(false);
  const [refinementSuccess, setRefinementSuccess] = useState<string | null>(null);

  const cargarPreview = useCallback(async () => {
    if (!proyectoId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await obtenerPreviewAppMovil(proyectoId);
      setAppData(data);
      const keys = Object.keys(data.archivos || {});
      if (keys.length > 0 && !selectedFile) {
        setSelectedFile(keys[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Error al cargar preview de la app móvil');
    } finally {
      setLoading(false);
    }
  }, [proyectoId, selectedFile]);

  const generar = useCallback(
    async (diagramJson: Record<string, any>, apiBaseUrl?: string, appName?: string) => {
      setLoading(true);
      setError(null);
      try {
        const data = await generarAppMovil(proyectoId, diagramJson, apiBaseUrl, appName);
        setAppData(data);
        const keys = Object.keys(data.archivos || {});
        if (keys.length > 0) {
          setSelectedFile(keys[0]);
        }
        return data;
      } catch (err: any) {
        setError(err.message || 'Error al generar la app móvil');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [proyectoId]
  );

  const refinar = useCallback(
    async (vistaNombre: string, codigoActual: string, instrucciones: string, apiEndpoint?: string) => {
      setRefining(true);
      setRefinementSuccess(null);
      setError(null);
      try {
        const res = await refinarVistaAppMovil({
          proyecto_id: proyectoId,
          vista_nombre: vistaNombre,
          codigo_actual: codigoActual,
          instrucciones,
          api_endpoint: apiEndpoint,
        });

        if (appData && selectedFile) {
          setAppData({
            ...appData,
            archivos: {
              ...appData.archivos,
              [selectedFile]: res.codigo_refinado,
            },
          });
        }
        setRefinementSuccess(res.resumen_cambios);
        return res;
      } catch (err: any) {
        setError(err.message || 'Error al refinar vista con IA');
        throw err;
      } finally {
        setRefining(false);
      }
    },
    [proyectoId, appData, selectedFile]
  );

  return {
    loading,
    error,
    appData,
    selectedFile,
    setSelectedFile,
    refining,
    refinementSuccess,
    cargarPreview,
    generar,
    refinar,
  };
}

