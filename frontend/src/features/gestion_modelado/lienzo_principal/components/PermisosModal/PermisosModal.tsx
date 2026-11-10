import React, { useCallback, useEffect, useState } from 'react';
import { useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { apiFetch } from '@/shared/lib/api';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import './PermisosModal.css';

interface Props {
  onClose: () => void;
  proyectoId: number;
}

/** CU38: miembro del proyecto con su permiso guardado en la base */
interface Miembro {
  usuario_id: number;
  nombre: string;
  rol_proyecto: string;
  permiso: 'edit' | 'view';
  nivel: 'lector' | 'editor' | 'anfitrion';
}

export const PermisosModal: React.FC<Props> = ({ onClose, proyectoId }) => {
  const { pendingGuests, roomUsers, approveGuest, requestRoomUsers, kickUser, changeUserRole } = useRealTimeSync();
  const [activeTab, setActiveTab] = useState<'pending' | 'users'>('pending');
  const [miembros, setMiembros] = useState<Miembro[]>([]);
  const [errorPermiso, setErrorPermiso] = useState<string | null>(null);

  const cargarMiembros = useCallback(() => {
    apiFetch<Miembro[]>(`/api/proyectos/${proyectoId}/miembros`).then(setMiembros).catch(() => {});
  }, [proyectoId]);

  useEffect(() => { cargarMiembros(); }, [cargarMiembros]);

  // El permiso se GUARDA en el proyecto (CU38): sigue igual al reconectarse o reiniciar el servidor
  const cambiarPermiso = async (m: Miembro, permiso: 'edit' | 'view') => {
    setErrorPermiso(null);
    setMiembros(prev => prev.map(x => (x.usuario_id === m.usuario_id ? { ...x, permiso } : x)));
    try {
      await apiFetch(`/api/proyectos/${proyectoId}/miembros/${m.usuario_id}/permiso`, {
        method: 'PUT',
        body: JSON.stringify({ permiso }),
      });
      requestRoomUsers();
    } catch (e) {
      setErrorPermiso(e instanceof Error ? e.message : 'No se pudo cambiar el permiso');
      cargarMiembros();
    }
  };

  const enLinea = (usuarioId: number) => roomUsers.some((u: any) => u.id === `auth_${usuarioId}` && u.isOnline);
  // Invitados sin cuenta conectados ahora: su permiso no se puede guardar (solo dura la sesión)
  const sinCuenta = roomUsers.filter((u: any) => !miembros.some(m => u.id === `auth_${m.usuario_id}`));

  useEffect(() => {
    requestRoomUsers();
    // Poll for updates every 3 seconds while modal is open
    const interval = setInterval(requestRoomUsers, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Modal
      isOpen
      onClose={onClose}
      width="560px"
      title={
        <>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          Gestión de la sala
        </>
      }
      footer={
        <button type="button" className="modal-btn" onClick={onClose}>Cerrar</button>
      }
    >
        <div className="permisos-tabs">
          <button 
            className={`permisos-tab ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span>En Espera ({pendingGuests.length})</span>
            {pendingGuests.length > 0 && <span className="permisos-badge-pulse">{pendingGuests.length}</span>}
          </button>

          <button 
            className={`permisos-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>Miembros ({miembros.length + sinCuenta.length})</span>
          </button>
        </div>

        <div className="permisos-body">
          {activeTab === 'pending' && (
            <div className="permisos-list">
              {pendingGuests.length === 0 ? (
                <div className="permisos-empty">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  <p>No hay solicitudes pendientes en la sala de espera.</p>
                </div>
              ) : (
                pendingGuests.map((guest: any) => (
                  <div key={guest.guest_id} className="permisos-item">
                    <div className="permisos-user-info">
                      <div className="permisos-avatar">
                        {guest.nickname?.charAt(0).toUpperCase() || 'U'}
                      </div>
                      <div className="permisos-user-details">
                        <span className="permisos-name">{guest.nickname}</span>
                        <span className="permisos-sub">Solicitud de ingreso</span>
                      </div>
                    </div>
                    <div className="permisos-actions">
                      <button 
                        className="btn-approve" 
                        onClick={() => approveGuest(guest.guest_id, true, proyectoId)}
                        title="Permitir acceso a la sala"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        <span>Permitir</span>
                      </button>

                      <button 
                        className="btn-reject" 
                        onClick={() => approveGuest(guest.guest_id, false, proyectoId)}
                        title="Rechazar solicitud"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                        <span>Rechazar</span>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div className="permisos-list">
              {errorPermiso && <div className="permisos-error" role="alert">{errorPermiso}</div>}
              {miembros.length === 0 && sinCuenta.length === 0 ? (
                <div className="permisos-empty">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                  </svg>
                  <p>Todavía no hay miembros en el proyecto.</p>
                </div>
              ) : (
                <>
                  {miembros.map(m => {
                    const online = enLinea(m.usuario_id);
                    const esAnfitrion = m.rol_proyecto === 'anfitrion';
                    return (
                      <div key={m.usuario_id} className="permisos-item">
                        <div className="permisos-user-info">
                          <span className={`permisos-status ${online ? 'online' : 'offline'}`} title={online ? 'Conectado' : 'Desconectado'} />
                          <div className="permisos-avatar">{m.nombre?.charAt(0).toUpperCase() || 'U'}</div>
                          <div className="permisos-user-details">
                            <span className="permisos-name">{m.nombre}</span>
                            <span className="permisos-sub">
                              {esAnfitrion ? 'Anfitrión' : m.permiso === 'view' ? 'Lector: ve y comenta' : 'Editor: cambia el diagrama y aprueba a la IA'}
                              {online ? ' · en línea' : ''}
                            </span>
                          </div>
                        </div>
                        <div className="permisos-actions">
                          {esAnfitrion ? (
                            <span className="permisos-fijo">Siempre edita</span>
                          ) : (
                            <select
                              value={m.permiso}
                              onChange={e => cambiarPermiso(m, e.target.value as 'edit' | 'view')}
                              className="permisos-role-select"
                              aria-label={`Permiso de ${m.nombre}`}
                            >
                              <option value="edit">Editor</option>
                              <option value="view">Lector</option>
                            </select>
                          )}
                          {!esAnfitrion && online && (
                            <button className="btn-kick" onClick={() => kickUser(`auth_${m.usuario_id}`)} title="Expulsar usuario de la sala">
                              Expulsar
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {sinCuenta.map((user: any) => (
                    <div key={user.id} className="permisos-item">
                      <div className="permisos-user-info">
                        <span className={`permisos-status ${user.isOnline ? 'online' : 'offline'}`} />
                        <div className="permisos-avatar">{user.nickname?.charAt(0).toUpperCase() || 'U'}</div>
                        <div className="permisos-user-details">
                          <span className="permisos-name">{user.nickname}</span>
                          <span className="permisos-sub">Invitado sin cuenta · el permiso dura solo esta sesión</span>
                        </div>
                      </div>
                      <div className="permisos-actions">
                        <select
                          value={user.role}
                          onChange={(e) => changeUserRole(user.id, e.target.value)}
                          className="permisos-role-select"
                          aria-label={`Permiso de ${user.nickname}`}
                        >
                          <option value="edit">Editor</option>
                          <option value="view">Lector</option>
                        </select>
                        <button className="btn-kick" onClick={() => kickUser(user.id)} title="Expulsar usuario de la sala">
                          Expulsar
                        </button>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
    </Modal>
  );
};
