import React, { useEffect, useState } from 'react';
import { useSalaSocket } from '@/features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext';
import './PermisosModal.css';

interface Props {
  onClose: () => void;
  proyectoId: number;
}

export const PermisosModal: React.FC<Props> = ({ onClose, proyectoId }) => {
  const { pendingGuests, roomUsers, approveGuest, requestRoomUsers, kickUser, changeUserRole } = useSalaSocket();
  const [activeTab, setActiveTab] = useState<'pending' | 'users'>('pending');

  useEffect(() => {
    requestRoomUsers();
    // Poll for updates every 3 seconds while modal is open
    const interval = setInterval(requestRoomUsers, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Gestión de Sala</h2>
        
        <div className="permisos-tabs">
          <button 
            className={`permisos-tab ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            En Espera ({pendingGuests.length})
          </button>
          <button 
            className={`permisos-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            Usuarios ({roomUsers.length})
          </button>
        </div>

        <div className="permisos-body">
          {activeTab === 'pending' && (
            <div className="permisos-list">
              {pendingGuests.length === 0 ? (
                <p className="permisos-empty">No hay solicitudes pendientes.</p>
              ) : (
                pendingGuests.map((guest: any) => (
                  <div key={guest.guest_id} className="permisos-item">
                    <span className="permisos-name">{guest.nickname}</span>
                    <div className="permisos-actions">
                      <button className="btn-approve" onClick={() => approveGuest(guest.guest_id, true, proyectoId)}>Permitir</button>
                      <button className="btn-reject" onClick={() => approveGuest(guest.guest_id, false, proyectoId)}>Rechazar</button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div className="permisos-list">
              {roomUsers.length === 0 ? (
                <p className="permisos-empty">No hay usuarios en la sala.</p>
              ) : (
                roomUsers.map((user: any) => (
                  <div key={user.id} className="permisos-item">
                    <div className="permisos-user-info">
                      <span className={`permisos-status ${user.isOnline ? 'online' : 'offline'}`} title={user.isOnline ? 'Conectado' : 'Desconectado'} />
                      <span className="permisos-name">{user.nickname}</span>
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
                      <button className="btn-kick" onClick={() => kickUser(user.id)}>Expulsar</button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <button className="btn-close-modal" onClick={onClose}>Cerrar</button>
      </div>
    </div>
  );
};
