import { useState, useEffect, useCallback } from 'react';
import { obtenerMisTareas, marcarTarea, type TareaIA } from '../services/equipoService';

export function useChecklistPanel(proyectoId: number) {
  const [tareas, setTareas] = useState<TareaIA[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const cargar = useCallback(async () => {
    if (!proyectoId) return;
    setLoading(true);
    try {
      const data = await obtenerMisTareas(proyectoId);
      setTareas(data);
    } catch {
      // sin tareas asignadas todavía
    } finally {
      setLoading(false);
    }
  }, [proyectoId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  useEffect(() => {
    const handleRefetch = () => cargar();
    window.addEventListener('refetch_tareas_ia', handleRefetch);
    return () => window.removeEventListener('refetch_tareas_ia', handleRefetch);
  }, [cargar]);

  const toggleTarea = async (tareaId: number, completada: boolean) => {
    const actualizada = await marcarTarea(tareaId, completada);
    setTareas(prev => prev.map(t => (t.id === actualizada.id ? actualizada : t)));
  };

  const completadas = tareas.filter(t => t.completada).length;
  const porcentaje = tareas.length > 0 ? Math.round((completadas / tareas.length) * 100) : 0;

  return { tareas, loading, open, setOpen, toggleTarea, completadas, porcentaje, cargar };
}
