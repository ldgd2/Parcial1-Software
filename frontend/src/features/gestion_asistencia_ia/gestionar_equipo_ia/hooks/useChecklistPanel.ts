import { useState, useEffect, useCallback } from 'react';
import { obtenerMisTareas as getMisTareasNew, obtenerTodasLasTareas as getTodasNew, marcarTarea as markTareaNew } from '@/features/gestion_asistencia_ia/repartir_tareas';
import { obtenerMisTareas, obtenerTodasLasTareas, marcarTarea, type TareaIA } from '../services/equipoService';

export function useChecklistPanel(proyectoId: number) {
  const [tareas, setTareas] = useState<TareaIA[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const cargar = useCallback(async () => {
    if (!proyectoId) return;
    setLoading(true);
    try {
      // 1. Probar nuevo caso de uso repartir_tareas
      let data: any = await getMisTareasNew(proyectoId).catch(() => []);
      if (!data || data.length === 0) {
        data = await getTodasNew(proyectoId).catch(() => []);
      }

      // 2. Fallback a servicio tradicional si no hay datos
      if (!data || data.length === 0) {
        data = await obtenerMisTareas(proyectoId).catch(() => []);
      }
      if (!data || data.length === 0) {
        data = await obtenerTodasLasTareas(proyectoId).catch(() => []);
      }

      setTareas(data || []);
    } catch {
      try {
        const fallback = await obtenerTodasLasTareas(proyectoId);
        setTareas(fallback || []);
      } catch {
        // Sin tareas registradas aún
      }
    } finally {
      setLoading(false);
    }
  }, [proyectoId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  useEffect(() => {
    if (open) {
      cargar();
    }
  }, [open, cargar]);

  useEffect(() => {
    const handleRefetch = () => cargar();
    window.addEventListener('refetch_tareas_ia', handleRefetch);
    return () => window.removeEventListener('refetch_tareas_ia', handleRefetch);
  }, [cargar]);

  const toggleTarea = async (tareaId: number, completada: boolean) => {
    setTareas(prev => prev.map(t => (t.id === tareaId ? { ...t, completada } : t)));
    try {
      const actualizada = await markTareaNew(tareaId, completada).catch(() => marcarTarea(tareaId, completada));
      setTareas(prev => prev.map(t => (t.id === (actualizada as any).id ? (actualizada as any) : t)));
    } catch {
      cargar();
    }
  };

  const completadas = tareas.filter(t => t.completada).length;
  const porcentaje = tareas.length > 0 ? Math.round((completadas / tareas.length) * 100) : 0;

  return { tareas, loading, open, setOpen, toggleTarea, completadas, porcentaje, cargar };
}
