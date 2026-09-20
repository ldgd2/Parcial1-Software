import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { salaService } from '@/features/gestion_salas/shared/services/salaService';
import { WS_URL } from '@/shared/lib/api';
import './UnirseView.css';

import { getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';

export const UnirseView: React.FC = () => {
  const { codigo } = useParams<{ codigo: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'aprobado' | 'pendiente' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [proyectoNombre, setProyectoNombre] = useState('la sala');
  const [nickname, setNickname] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!codigo) { navigate('/dashboard'); return; }

    let isLogged = false;
    import('@/shared/lib/TokenService').then(({ TokenService }) => {
      isLogged = !!TokenService.getToken();
      
      let intervalId: any;

      if (isLogged) {
        salaService.unirse(codigo)
        .then((data: any) => {
          setProyectoNombre(data.proyecto_nombre || 'la sala');
          if (data.acceso === 'aprobado') {
            setStatus('aprobado');
            setTimeout(() => navigate(`/diagrama/${data.proyecto_id}`), 1500);
          } else {
            setStatus('pendiente');
            setMessage(data.mensaje || 'Esperando aprobación del anfitrión de la sala...');
            
            intervalId = setInterval(() => {
              salaService.unirse(codigo)
                .then((pollData: any) => {
                  if (pollData.acceso === 'aprobado') {
                    clearInterval(intervalId);
                    setStatus('aprobado');
                    setTimeout(() => navigate(`/diagrama/${pollData.proyecto_id}`), 1500);
                  } else if (pollData.acceso === 'rechazado' || pollData.acceso === 'error') {
                    clearInterval(intervalId);
                    setStatus('error');
                    setMessage('El anfitrión ha rechazado tu solicitud de ingreso.');
                  }
                })
                .catch(() => {
                  clearInterval(intervalId);
                  setStatus('error');
                  setMessage('Error al verificar el estado de la solicitud.');
                });
            }, 3000);
          }
        })
        .catch((err: any) => {
          setStatus('error');
          setMessage(err.message || 'Código de acceso inválido o no tienes acceso.');
        });
      } else {
        // Guest flow
        const identity = getUserIdentity();
        setNickname(identity.nickname);
        
        const wsUrl = `${WS_URL}/ws/salas/${codigo}?user_type=guest&guest_id=${identity.id}&nickname=${encodeURIComponent(identity.nickname)}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setStatus('pendiente');
          setMessage(`Te has conectado como ${identity.isRegistered ? 'usuario' : 'invitado'}: "${identity.nickname}". Esperando autorización...`);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'admission_status') {
              if (data.approved) {
                setStatus('aprobado');
                setTimeout(() => navigate(`/diagrama/${data.proyecto_id}?guest=true&codigo=${codigo}`), 1500);
              } else {
                setStatus('error');
                setMessage('El anfitrión ha rechazado tu solicitud de acceso.');
                ws.close();
              }
            }
          } catch (e) {
            console.error(e);
          }
        };

        ws.onerror = () => {
          setStatus('error');
          setMessage('Error al conectar por tiempo real con la sala. Verifica el código.');
        };

        return () => {
          if (wsRef.current) {
            wsRef.current.close();
          }
          if (intervalId) {
            clearInterval(intervalId);
          }
        };
      }
    });
  }, [codigo, navigate]);

  return (
    <div className="unirse-view">
      <div className="unirse-view__ambient-glow" />
      
      <div className="unirse-card">
        <div className="unirse-card__header">
          <div className="unirse-card__badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
            SALA DE COLABORACIÓN
          </div>
          <span className="unirse-card__code">código: #{codigo}</span>
        </div>

        <div className={`unirse-card__icon-wrapper unirse-card__icon-wrapper--${status}`}>
          {status === 'loading' && (
            <svg className="unirse-card__svg-icon spin" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
          )}
          {status === 'aprobado' && (
            <svg className="unirse-card__svg-icon pulse" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          )}
          {status === 'pendiente' && (
            <svg className="unirse-card__svg-icon pulse-glow" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="9"/>
              <path d="M12 7v5l3 3"/>
            </svg>
          )}
          {status === 'error' && (
            <svg className="unirse-card__svg-icon shake" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          )}
        </div>

        {status === 'loading' && (
          <div className="unirse-card__body">
            <h2>Estableciendo conexión...</h2>
            <p>Verificando credenciales y estado del servidor de colaboración.</p>
          </div>
        )}

        {status === 'aprobado' && (
          <div className="unirse-card__body">
            <h2 className="unirse-title--success">¡Acceso Concedido!</h2>
            <p>Entrando a la sala de modelado UML <strong>{proyectoNombre}</strong>...</p>
            <div className="unirse-progress-bar">
              <div className="unirse-progress-fill" />
            </div>
          </div>
        )}

        {status === 'pendiente' && (
          <div className="unirse-card__body">
            <h2>Sala de Espera Interactiva</h2>
            <p className="unirse-message">{message}</p>

            {nickname && (
              <div className="unirse-user-pill">
                <span className="unirse-user-dot" />
                <span>Modo Invitado: <strong>{nickname}</strong></span>
              </div>
            )}

            <div className="unirse-waiting-indicator">
              <span className="dot dot-1" />
              <span className="dot dot-2" />
              <span className="dot dot-3" />
            </div>

            <button
              className="unirse-card__btn-cancel"
              onClick={() => navigate('/dashboard')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              Cancelar y Volver
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="unirse-card__body">
            <h2 className="unirse-title--error">Acceso Restringido</h2>
            <p className="unirse-message">{message}</p>
            <button
              className="unirse-card__btn-primary"
              onClick={() => navigate('/dashboard')}
            >
              Volver al Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
