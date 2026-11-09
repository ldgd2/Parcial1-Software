import { useCallback, useEffect, useRef, useState } from 'react';
import type { VersionDetalle, VersionResumen } from '../types';
import { listarVersiones, obtenerVersion } from '../services/contextoService';

/** Evento que se emite cuando la IA (o una restauración) registra una versión nueva. */
export const EVENTO_VERSIONES_ACTUALIZADAS = 'contexto_ia_versiones_actualizadas';

const PAGINA = 30;

export function useVersionesContexto(proyectoId: number | undefined, activo: boolean) {
  const [versiones, setVersiones] = useState<VersionResumen[]>([]);
  const [hayMas, setHayMas] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detalles, setDetalles] = useState<Record<number, VersionDetalle>>({});
  const [cargandoDetalle, setCargandoDetalle] = useState<number | null>(null);
  const pedidos = useRef(new Set<number>());

  const valido = !!proyectoId && proyectoId > 0;

  const recargar = useCallback(async () => {
    if (!valido) return;
    setCargando(true);
    setError(null);
    try {
      const pag = await listarVersiones(proyectoId!, PAGINA);
      setVersiones(pag.items);
      setHayMas(pag.hay_mas);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar el historial');
    } finally {
      setCargando(false);
    }
  }, [proyectoId, valido]);

  const cargarMas = useCallback(async () => {
    if (!valido || !versiones.length || cargando) return;
    setCargando(true);
    try {
      const pag = await listarVersiones(proyectoId!, PAGINA, versiones[versiones.length - 1].id);
      setVersiones(prev => [...prev, ...pag.items.filter(v => !prev.some(p => p.id === v.id))]);
      setHayMas(pag.hay_mas);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar más historial');
    } finally {
      setCargando(false);
    }
  }, [proyectoId, valido, versiones, cargando]);

  const cargarDetalle = useCallback(async (versionId: number, forzar = false) => {
    if (!valido) return;
    if (!forzar && (detalles[versionId] || pedidos.current.has(versionId))) return;
    pedidos.current.add(versionId);
    setCargandoDetalle(versionId);
    try {
      const d = await obtenerVersion(proyectoId!, versionId);
      setDetalles(prev => ({ ...prev, [versionId]: d }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar la versión');
    } finally {
      pedidos.current.delete(versionId);
      setCargandoDetalle(cur => (cur === versionId ? null : cur));
    }
  }, [proyectoId, valido, detalles]);

  // Cargar al abrir el modal
  useEffect(() => {
    if (activo) recargar();
  }, [activo, recargar]);

  // Refrescar cuando llega una versión nueva o se completa el "después" de una existente
  useEffect(() => {
    const alActualizar = (e: Event) => {
      const id = (e as CustomEvent<{ versionId?: number }>).detail?.versionId;
      if (id) {
        setDetalles(prev => {
          const copia = { ...prev };
          delete copia[id];
          return copia;
        });
      }
      if (activo) recargar();
    };
    window.addEventListener(EVENTO_VERSIONES_ACTUALIZADAS, alActualizar);
    return () => window.removeEventListener(EVENTO_VERSIONES_ACTUALIZADAS, alActualizar);
  }, [activo, recargar]);

  return { versiones, hayMas, cargando, error, detalles, cargandoDetalle, recargar, cargarMas, cargarDetalle };
}
