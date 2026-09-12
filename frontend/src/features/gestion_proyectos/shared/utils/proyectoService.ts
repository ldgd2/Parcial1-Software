import { apiFetch } from '@/shared/lib/api';


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
  compartirProyecto: async (id: number, data: any) => {
    return await apiFetch(`/proyectos/${id}/compartir`, { method: 'POST', body: JSON.stringify(data) });
  },
  getLinkInvitacion: (codigo?: string) => {
    return `${window.location.origin}/unirse/${codigo || ''}`;
  }
};
