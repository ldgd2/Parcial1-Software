import { apiFetch } from '@/shared/lib/api';
import type { Miembro } from './types';


export const proyectoService = {
  listar: async () => {
    return await apiFetch('/proyectos/mis-proyectos');
  },
  crear: async (nombre: string, descripcion: string) => {
    return await apiFetch('/proyectos/', { method: 'POST', body: JSON.stringify({ nombre, descripcion }) });
  },
  actualizar: async (id: number, nombre: string, descripcion: string) => {
    return await apiFetch(`/proyectos/${id}`, { method: 'PUT', body: JSON.stringify({ nombre, descripcion }) });
  },
  eliminar: async (id: number) => {
    return await apiFetch(`/proyectos/${id}`, { method: 'DELETE' });
  },
  /** CU08: comparte el proyecto con un usuario registrado */
  invitar: async (id: number, email: string, permiso: 'editor' | 'lector'): Promise<Miembro> => {
    return await apiFetch(`/proyectos/${id}/invitar`, { method: 'POST', body: JSON.stringify({ email, permiso }) });
  },
  miembros: async (id: number): Promise<Miembro[]> => {
    return await apiFetch(`/proyectos/${id}/miembros`);
  },
  cambiarPermiso: async (id: number, usuarioId: number, permiso: 'editor' | 'lector'): Promise<Miembro> => {
    return await apiFetch(`/proyectos/${id}/miembros/${usuarioId}/permiso`, { method: 'PUT', body: JSON.stringify({ permiso }) });
  },
  compartidosConmigo: async () => {
    return await apiFetch('/proyectos/compartidos-conmigo');
  },
  getLinkInvitacion: (codigo?: string) => {
    return `${window.location.origin}/unirse/${codigo || ''}`;
  }
};
