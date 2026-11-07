import { useState, useEffect, useCallback } from 'react';
import type {
  ContextoIAResponse,
  CompilarContextoResponse,
  RegistrarInteraccionPayload
} from '../types';
import {
  obtenerContextoProyecto,
  registrarInteraccion,
  guardarSnapshotDiagrama,
  compilarContextoLlm,
  limpiarMemoriaContexto
} from '../services/contextoService';

interface UseContextoPersistenteProps {
  proyectoId?: number;
}

export function useContextoPersistente({ proyectoId }: UseContextoPersistenteProps) {
  const [contexto, setContexto] = useState<ContextoIAResponse | null>(null);
  const [compilado, setCompilado] = useState<CompilarContextoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const cargarContexto = useCallback(async () => {
    if (!proyectoId || proyectoId <= 0) return;
    setLoading(true);
    setError(null);
    try {
      const data = await obtenerContextoProyecto(proyectoId);
      setContexto(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error cargando contexto persistente';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [proyectoId]);

  const cargarCompilado = useCallback(async () => {
    if (!proyectoId || proyectoId <= 0) return;
    try {
      const comp = await compilarContextoLlm(proyectoId);
      setCompilado(comp);
    } catch (err) {
      console.warn('[useContextoPersistente] Error compilando contexto:', err);
    }
  }, [proyectoId]);

  const guardarInteraccion = useCallback(async (payload: Omit<RegistrarInteraccionPayload, 'proyecto_id'>) => {
    if (!proyectoId || proyectoId <= 0) return null;
    try {
      const data = await registrarInteraccion({
        ...payload,
        proyecto_id: proyectoId
      });
      setContexto(data);
      return data;
    } catch (err) {
      console.error('[useContextoPersistente] Error registrando interacción:', err);
      return null;
    }
  }, [proyectoId]);

  const sincronizarSnapshot = useCallback(async (dsl: string, dominio?: string, resumen?: string) => {
    if (!proyectoId || proyectoId <= 0) return null;
    try {
      const data = await guardarSnapshotDiagrama(proyectoId, dsl, dominio, resumen);
      setContexto(data);
      return data;
    } catch (err) {
      console.error('[useContextoPersistente] Error sincronizando snapshot:', err);
      return null;
    }
  }, [proyectoId]);

  const reiniciarMemoria = useCallback(async (conservarDominio: boolean = true) => {
    if (!proyectoId || proyectoId <= 0) return null;
    setLoading(true);
    try {
      const data = await limpiarMemoriaContexto(proyectoId, conservarDominio);
      setContexto(data);
      return data;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error reiniciando memoria';
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, [proyectoId]);

  useEffect(() => {
    if (proyectoId && proyectoId > 0) {
      cargarContexto();
    }
  }, [proyectoId, cargarContexto]);

  return {
    contexto,
    compilado,
    loading,
    error,
    isModalOpen,
    setIsModalOpen,
    cargarContexto,
    cargarCompilado,
    guardarInteraccion,
    sincronizarSnapshot,
    reiniciarMemoria
  };
}

