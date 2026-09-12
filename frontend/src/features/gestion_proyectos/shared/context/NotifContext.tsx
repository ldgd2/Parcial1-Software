import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { Notificacion } from '../utils/types';
import { ToastStack } from '@/features/gestion_proyectos/administrar_proyecto/components/ToastStack/ToastStack';

interface NotifContextValue {
  notificar: (notif: { titulo: string; mensaje: string; tipo: Notificacion['tipo'] }) => void;
  eliminar: (id: string) => void;
  notificaciones: Notificacion[];
}

const NotifContext = createContext<NotifContextValue | undefined>(undefined);

export const NotifProvider = ({ children }: { children: ReactNode }) => {
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);

  const notificar = ({ titulo, mensaje, tipo }: { titulo: string; mensaje: string; tipo: Notificacion['tipo'] }) => {
    const id = Math.random().toString(36).substring(7);
    setNotificaciones(prev => [...prev, { id, titulo, mensaje, tipo }]);
    setTimeout(() => {
      setNotificaciones(prev => prev.filter(n => n.id !== id));
    }, 3000);
  };

  const eliminar = (id: string) => {
    setNotificaciones(prev => prev.filter(n => n.id !== id));
  };

  return (
    <NotifContext.Provider value={{ notificar, eliminar, notificaciones }}>
      {children}
      <ToastStack />
    </NotifContext.Provider>
  );
};

export const useNotif = () => {
  const ctx = useContext(NotifContext);
  if (!ctx) throw new Error('useNotif must be used within NotifProvider');
  return ctx;
};
