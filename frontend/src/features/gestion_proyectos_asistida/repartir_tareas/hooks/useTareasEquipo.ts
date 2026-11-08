import { useState, useCallback, useEffect } from 'react';
import { tareasService } from '../services/tareasService';
import type { TareaItem, RepartirTareasRequest, CrearTareaManualRequest } from '../types';

export function useTareasEquipo(proyectoId?: number) {
  const [tareas, setTareas] = useState<TareaItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const cargarTodas = useCallback(async () => {
    if (!proyectoId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await tareasService.obtenerTodasLasTareas(proyectoId);
      setTareas(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar tareas';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [proyectoId]);

  useEffect(() => {
    cargarTodas();
  }, [cargarTodas]);

  const repartirConIA = useCallback(
    async (req: Omit<RepartirTareasRequest, 'proyecto_id'>) => {
      if (!proyectoId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await tareasService.repartirTareasEquipo({
          ...req,
          proyecto_id: proyectoId,
        });
        setTareas(res.tareas || []);
        return res;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Error al generar tareas con IA';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [proyectoId]
  );

  const toggleTarea = useCallback(async (tareaId: number, completada: boolean) => {
    try {
      const updated = await tareasService.marcarTarea(tareaId, completada);
      setTareas((prev) => prev.map((t) => (t.id === tareaId ? updated : t)));
      return updated;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cambiar estado de la tarea';
      setError(msg);
      throw err;
    }
  }, []);

  const crearManual = useCallback(
    async (req: Omit<CrearTareaManualRequest, 'proyecto_id'>) => {
      if (!proyectoId) return;
      try {
        const nueva = await tareasService.crearTareaManual({
          ...req,
          proyecto_id: proyectoId,
        });
        setTareas((prev) => [...prev, nueva]);
        return nueva;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Error al crear tarea manual';
        setError(msg);
        throw err;
      }
    },
    [proyectoId]
  );

  const eliminar = useCallback(async (tareaId: number) => {
    try {
      await tareasService.eliminarTarea(tareaId);
      setTareas((prev) => prev.filter((t) => t.id !== tareaId));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al eliminar tarea';
      setError(msg);
      throw err;
    }
  }, []);

  return {
    tareas,
    loading,
    error,
    cargarTodas,
    repartirConIA,
    toggleTarea,
    crearManual,
    eliminar,
  };
}

