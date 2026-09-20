import React, { useEffect, useState } from 'react';
import { useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import './PermisosModal.css';

interface Props {
  onClose: () => void;
  proyectoId: number;
}

export const PermisosModal: React.FC<Props> = ({ onClose, proyectoId }) => {
  const { pendingGuests, roomUsers, approveGuest, requestRoomUsers, kickUser, changeUserRole } = useRealTimeSync();
  const [activeTab, setActiveTab] = useState<'pending' | 'users'>('pending');

  useEffect(() => {
    requestRoomUsers();
    // Poll for updates every 3 seconds while modal is open
    const interval = setInterval(requestRoomUsers, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="permisos-modal-backdrop" onClick={onClose}>
      <div className="permisos-modal-card" onClick={e => e.stopPropagation()}>
        <div className="permisos-modal-header">
          <div className="permisos-modal-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <h2>Gestión de Sala de Colaboración</h2>
          </div>
          <button className="permisos-modal-close-icon" onClick={onClose} title="Cerrar modal">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

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
            <span>Conectados ({roomUsers.length})</span>
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
              {roomUsers.length === 0 ? (
                <div className="permisos-empty">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                  </svg>
                  <p>No hay colaboradores activos en este momento.</p>
                </div>
              ) : (
                roomUsers.map((user: any) => (
                  <div key={user.id} className="permisos-item">
                    <div className="permisos-user-info">
                      <span className={`permisos-status ${user.isOnline ? 'online' : 'offline'}`} title={user.isOnline ? 'Conectado' : 'Desconectado'} />
                      <div className="permisos-avatar">
                        {user.nickname?.charAt(0).toUpperCase() || 'U'}
                      </div>
                      <div className="permisos-user-details">
                        <span className="permisos-name">{user.nickname}</span>
                        <span className="permisos-sub">{user.isOnline ? 'En línea' : 'Desconectado'}</span>
                      </div>
                    </div>
                    <div className="permisos-actions">
                      <select 
                        value={user.role} 
                        onChange={(e) => changeUserRole(user.id, e.target.value)}
                        className="permisos-role-select"
                      >
                        <option value="edit">Editor</option>
                        <option value="view">Lector</option>
                      </select>
                      <button 
                        className="btn-kick" 
                        onClick={() => kickUser(user.id)}
                        title="Expulsar usuario de la sala"
                      >
                        Expulsar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="permisos-modal-footer">
          <button className="btn-close-modal" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
