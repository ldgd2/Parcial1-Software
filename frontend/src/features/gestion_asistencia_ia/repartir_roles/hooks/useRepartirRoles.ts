import { useState, useCallback, useEffect } from 'react';
import { rolesService } from '../services/rolesService';
import type { ColaboradorRolOut, RepartirRolesRequest, AsignarRolManualRequest } from '../types';

export function useRepartirRoles(proyectoId?: number) {
  const [roles, setRoles] = useState<ColaboradorRolOut[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const cargarRoles = useCallback(async () => {
    if (!proyectoId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await rolesService.obtenerRolesProyecto(proyectoId);
      setRoles(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar roles del proyecto';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [proyectoId]);

  useEffect(() => {
    cargarRoles();
  }, [cargarRoles]);

  const repartirConIA = useCallback(
    async (req: Omit<RepartirRolesRequest, 'proyecto_id'>) => {
      if (!proyectoId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await rolesService.repartirRolesEquipo({
          ...req,
          proyecto_id: proyectoId,
        });
        setRoles(res.roles || []);
        return res;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Error al repartir roles con IA';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [proyectoId]
  );

  const asignarManual = useCallback(
    async (req: Omit<AsignarRolManualRequest, 'proyecto_id'>) => {
      if (!proyectoId) return;
      setLoading(true);
      setError(null);
      try {
        const updated = await rolesService.asignarRolManual({
          ...req,
          proyecto_id: proyectoId,
        });
        setRoles((prev) =>
          prev.map((r) => (r.usuario_id === updated.usuario_id ? updated : r))
        );
        return updated;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Error al asignar rol manualmente';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [proyectoId]
  );

  return {
    roles,
    loading,
    error,
    cargarRoles,
    repartirConIA,
    asignarManual,
  };
}

