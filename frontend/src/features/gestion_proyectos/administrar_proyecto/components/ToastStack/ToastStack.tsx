import React, { useEffect, useState } from 'react';
import { useNotif } from '@/features/gestion_proyectos/shared/context/NotifContext';
import type { Notificacion } from '@/features/gestion_proyectos/shared/utils/types';
import './ToastStack.css';

const iconos: Record<Notificacion['tipo'], React.ReactNode> = {
  exito: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6L9 17l-5-5"/></svg>,
  error: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>,
  info: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>,
  advertencia: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"/></svg>,
};

const Toast: React.FC<{ notif: Notificacion; onClose: () => void }> = ({ notif, onClose }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  return (
    <div className={`toast toast--${notif.tipo} ${visible ? 'toast--visible' : ''}`}>
      <div className="toast__icon">{iconos[notif.tipo]}</div>
      <div className="toast__content">
        <div className="toast__title">{notif.titulo}</div>
        <div className="toast__msg">{notif.mensaje}</div>
      </div>
      <button className="toast__close" onClick={onClose}><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
  );
};

export const ToastStack: React.FC = () => {
  const { notificaciones, eliminar } = useNotif();
  return (
    <div className="toast-stack">
      {notificaciones.map(n => (
        <Toast key={n.id} notif={n} onClose={() => eliminar(n.id)} />
      ))}
    </div>
  );
};
