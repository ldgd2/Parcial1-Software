import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { salaService } from '@/features/gestion_salas/shared/services/salaService';
import { getGuestId, getGuestNickname } from '@/shared/utils/animalNames';
import './UnirseView.css';

export const UnirseView: React.FC = () => {
  const { codigo } = useParams<{ codigo: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'aprobado' | 'pendiente' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [proyectoNombre, setProyectoNombre] = useState('la sala');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!codigo) { navigate('/dashboard'); return; }

    const isLogged = !!localStorage.getItem('access_token');
    
    let intervalId: any;

    if (isLogged) {
      // Authenticated flow
      salaService.unirse(codigo)
        .then((data: any) => {
          setProyectoNombre(data.proyecto_nombre || 'la sala');
          if (data.acceso === 'aprobado') {
            setStatus('aprobado');
            setTimeout(() => navigate(`/diagrama/${data.proyecto_id}`), 1500);
          } else {
            setStatus('pendiente');
            setMessage(data.mensaje);
            
            // Poll for approval status
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
                    setMessage('El anfitrión ha rechazado tu solicitud.');
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
          setMessage(err.message || 'Código inválido o sin acceso.');
        });
    } else {
      // Guest flow
      const guestId = getGuestId();
      const nickname = getGuestNickname();
      
      const wsUrl = `ws://localhost:8000/ws/salas/${codigo}?user_type=guest&guest_id=${guestId}&nickname=${encodeURIComponent(nickname)}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('pendiente');
        setMessage(`Estás conectado como ${nickname}. Esperando a que el anfitrión te permita entrar...`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'admission_status') {
            if (data.approved) {
              setStatus('aprobado');
              // Navigate to the diagram view. The SalaSocketContext will reconnect.
              setTimeout(() => navigate(`/diagrama/${data.proyecto_id}?guest=true&codigo=${codigo}`), 1500);
            } else {
              setStatus('error');
              setMessage('El anfitrión ha rechazado tu solicitud.');
              ws.close();
            }
          }
        } catch (e) {
          console.error(e);
        }
      };

      ws.onerror = () => {
        setStatus('error');
        setMessage('Error al conectar con la sala. Verifica el código.');
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
  }, [codigo, navigate]);

  return (
    <div className="unirse-view">
      <div className="unirse-card">
        <div className={`unirse-card__icon unirse-card__icon--${status}`}><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></div>

        {status === 'loading' && (
          <>
            <div className="unirse-spinner" />
            <h2>Conectando...</h2>
          </>
        )}

        {status === 'aprobado' && (
          <>
            <h2>ACCESO CONCEDIDO</h2>
            <p>Entrando a <strong>{proyectoNombre}</strong>...</p>
            <div className="unirse-progress" />
          </>
        )}

        {status === 'pendiente' && (
          <>
            <h2>SALA DE ESPERA</h2>
            <p>{message}</p>
            <div className="unirse-spinner" style={{ margin: '20px auto', width: '30px', height: '30px' }} />
            <button
              className="unirse-card__btn"
              onClick={() => navigate('/dashboard')}
            >
              CANCELAR Y SALIR
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <h2>ERROR DE ACCESO</h2>
            <p>{message}</p>
            <button
              className="unirse-card__btn"
              onClick={() => navigate('/dashboard')}
            >
              VOLVER AL INICIO
            </button>
          </>
        )}
      </div>
    </div>
  );
};
