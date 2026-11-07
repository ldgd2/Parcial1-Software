import { useState, useEffect, useCallback } from 'react';
import type { ComentarioElemento } from '../types';
import {
  listarComentariosElemento,
  listarTodosComentariosProyecto,
  crearComentarioElemento,
  actualizarComentarioElemento,
  eliminarComentarioElemento
} from '../services/comentarService';

interface UseComentarElementoProps {
  proyectoId?: number;
  elementoId?: string;
}

export function useComentarElemento({ proyectoId, elementoId }: UseComentarElementoProps) {
  const [comentarios, setComentarios] = useState<ComentarioElemento[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarComentarios = useCallback(async () => {
    if (!proyectoId || proyectoId <= 0) return;
    setLoading(true);
    setError(null);
    try {
      if (elementoId) {
        const data = await listarComentariosElemento(proyectoId, elementoId);
        setComentarios(data);
      } else {
        const data = await listarTodosComentariosProyecto(proyectoId);
        setComentarios(data);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error cargando comentarios';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [proyectoId, elementoId]);

  const agregarComentario = useCallback(
    async (texto: string, elementoTipo: 'node' | 'relation' = 'node', autorNombre?: string) => {
      if (!proyectoId || !elementoId || !texto.trim()) return null;
      try {
        const nuevo = await crearComentarioElemento({
          proyecto_id: proyectoId,
          elemento_id: elementoId,
          elemento_tipo: elementoTipo,
          texto: texto.trim(),
          autor_nombre: autorNombre || 'Colaborador'
        });
        setComentarios(prev => [...prev, nuevo]);
        return nuevo;
      } catch (err) {
        console.error('[useComentarElemento] Error agregando comentario:', err);
        return null;
      }
    },
    [proyectoId, elementoId]
  );

  const cambiarEstado = useCallback(
    async (comentarioId: string, nuevoEstado: 'abierto' | 'resuelto') => {
      try {
        const updated = await actualizarComentarioElemento(comentarioId, { estado: nuevoEstado });
        setComentarios(prev => prev.map(c => (c.id === comentarioId ? updated : c)));
        return updated;
      } catch (err) {
        console.error('[useComentarElemento] Error cambiando estado:', err);
        return null;
      }
    },
    []
  );

  const borrarComentario = useCallback(async (comentarioId: string) => {
    try {
      await eliminarComentarioElemento(comentarioId);
      setComentarios(prev => prev.filter(c => c.id !== comentarioId));
      return true;
    } catch (err) {
      console.error('[useComentarElemento] Error eliminando comentario:', err);
      return false;
    }
  }, []);

  useEffect(() => {
    if (proyectoId && proyectoId > 0) {
      cargarComentarios();
    }
  }, [proyectoId, elementoId, cargarComentarios]);

  return {
    comentarios,
    loading,
    error,
    cargarComentarios,
    agregarComentario,
    cambiarEstado,
    borrarComentario
  };
}

