import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { getGuestId, getGuestNickname } from '@/shared/utils/animalNames';
import { useSearchParams } from 'react-router-dom';
import { WS_URL } from '@/shared/lib/api';

import { TokenService } from '@/shared/lib/TokenService';

export const getUserIdentity = (): { id: string; nickname: string; isRegistered: boolean } => {
  const token = TokenService.getToken();
  const storedName = localStorage.getItem('usuario_nombre');
  const userStr = localStorage.getItem('user');

  let registeredUser: any = null;
  if (userStr) {
    try {
      registeredUser = JSON.parse(userStr);
    } catch (e) {}
  }

  if (token) {
    const nickname = registeredUser?.nombre || storedName || registeredUser?.email?.split('@')[0] || 'Usuario';
    const id = registeredUser?.id ? `auth_${registeredUser.id}` : `auth_${nickname.replace(/\s+/g, '_')}`;
    return { id, nickname, isRegistered: true };
  }

  return {
    id: getGuestId(),
    nickname: getGuestNickname(),
    isRegistered: false
  };
};

interface PendingGuest {
  guest_id: string;
  nickname: string;
}

interface Cursor {
  x: number;
  y: number;
  nickname: string;
}

interface RealTimeSyncContextType {
  socket: WebSocket | null;
  pendingGuests: PendingGuest[];
  cursors: Record<string, Cursor>;
  lockedElements: Record<string, string>; // element_id -> nickname
  lockElement: (elementId: string) => void;
  refreshLock: (elementId: string) => void;
  unlockElement: (elementId: string) => void;
  approveGuest: (guestId: string, approved: boolean, proyectoId: number) => void;
  broadcastDiagramEvent: (event: any) => void;
  broadcastDiagramDelta: (head: string, objects: Record<string, any>) => void;
  roomUsers: any[];
  requestRoomUsers: () => void;
  kickUser: (guestId: string) => void;
  changeUserRole: (guestId: string, role: string) => void;
  isReadOnly: boolean;
}

const RealTimeSyncContext = createContext<RealTimeSyncContextType | null>(null);

export const RealTimeSyncProvider: React.FC<{ children: React.ReactNode; sala: any }> = ({ children, sala }) => {
  const [pendingGuests, setPendingGuests] = useState<PendingGuest[]>([]);
  const [cursors, setCursors] = useState<Record<string, Cursor>>({});
  const [lockedElements, setLockedElements] = useState<Record<string, string>>({});
  const [roomUsers, setRoomUsers] = useState<any[]>([]);
  const [isReadOnly, setIsReadOnly] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const socketRef = useRef<WebSocket | null>(null);
  
  const [searchParams] = useSearchParams();
  const isGuest = searchParams.get('guest') === 'true' || (sala.rol_proyecto && sala.rol_proyecto !== 'anfitrion');
  const codigo = searchParams.get('codigo') || sala.codigo_acceso;

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Auto-fetch profile if logged in but local storage is missing user data
  useEffect(() => {
    const token = TokenService.getToken();
    if (token && (!localStorage.getItem('user') || !localStorage.getItem('usuario_nombre'))) {
      import('@/shared/lib/api').then(({ apiFetch }) => {
        apiFetch('/usuarios/me').then(user => {
          if (user) {
            localStorage.setItem('user', JSON.stringify(user));
            if (user.nombre) {
              localStorage.setItem('usuario_nombre', user.nombre);
            }
          }
        }).catch(() => {});
      });
    }
  }, []);

  useEffect(() => {
    if (sala.codigo_acceso === 'local' || !isOnline) {
      console.log('Modo offline detectado: WebSocket omitido.');
      return;
    }
    
    const identity = getUserIdentity();
    let wsUrl = `${WS_URL}/ws/salas/${codigo}`;
    
    if (isGuest) {
      wsUrl += `?user_type=guest&guest_id=${identity.id}&nickname=${encodeURIComponent(identity.nickname)}`;
    } else {
      wsUrl += `?user_type=host&guest_id=${identity.id}&nickname=${encodeURIComponent(identity.nickname)}`;
    }

    let ws: WebSocket | null = null;
    let reconnectTimeout: any;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = async () => {
        console.log('WebSocket connected');
        
        try {
          const { offlineSyncService } = await import('@/features/gestion_concurrencia/sincronizar_estado_local/services/OfflineSyncService');
          const allObjects = offlineSyncService.getAll();
          const objectsPayload: Record<string, any> = {};
          allObjects.forEach((val, key) => {
            if (key !== 'DIAGRAMA_LOCAL') {
              objectsPayload[key] = val;
            }
          });
          
          if (Object.keys(objectsPayload).length > 0) {
            ws!.send(JSON.stringify({
              type: 'sync_offline',
              objects: objectsPayload,
              head: 'sync_' + Date.now()
            }));
          }
        } catch (e) {
          console.error("Error syncing offline objects", e);
        }

        // Pedir al servidor los snapshots de versiones actuales
        ws!.send(JSON.stringify({ type: 'request_snapshots' }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'join_request':
              setPendingGuests(prev => {
                if (prev.find(g => g.guest_id === data.guest_id)) return prev;
                return [...prev, { guest_id: data.guest_id, nickname: data.nickname }];
              });
              break;
              
            case 'guest_left':
              setPendingGuests(prev => prev.filter(g => g.guest_id !== data.guest_id));
              setCursors(prev => {
                const newCursors = { ...prev };
                delete newCursors[data.guest_id];
                return newCursors;
              });
              break;
              
            case 'mouse_move':
              setCursors(prev => ({
                ...prev,
                [data.user_id]: { x: data.x, y: data.y, nickname: data.nickname }
              }));
              break;
              
            case 'snapshots_response':
              // El servidor devolvió el estado actual de todas las clases
              // Disparar el evento que DiagramContext escucha para hacer el diff
              window.dispatchEvent(new CustomEvent('vcs_server_sync', {
                detail: { snapshots: data.snapshots }
              }));
              break;

            case 'diagram_delta':
              // Guardar todos los nuevos objetos en la IndexedDB/Cache local
              if (data.objects && data.head) {
                // Dynamic import para no romper si OfflineSyncService no está listo
                import('@/features/gestion_concurrencia/sincronizar_estado_local/services/OfflineSyncService').then(({ offlineSyncService }) => {
                  Object.keys(data.objects).forEach(hash => {
                    offlineSyncService.putObject(hash, data.objects[hash]);
                  });
                  // Notificar al frontend que llegaron deltas para que redibuje el head
                  window.dispatchEvent(new CustomEvent('remote_diagram_delta', { detail: { head: data.head } }));
                });
              }
              break;
              
            case 'room_users_list':
              setRoomUsers(data.users);
              break;
            case 'user_kicked':
              setRoomUsers(prev => prev.filter(u => u.id !== data.guest_id));
              break;
            case 'role_updated':
              setRoomUsers(prev => prev.map(u => u.id === data.guest_id ? { ...u, role: data.role } : u));
              break;
            case 'role_changed':
              setIsReadOnly(data.role === 'view');
              break;
            case 'kicked':
              alert('Has sido expulsado de la sala.');
              window.location.href = '/dashboard';
              break;
            case 'element_locked':
              setLockedElements(prev => ({
                ...prev,
                [data.element_id]: data.nickname
              }));
              break;
            case 'element_unlocked':
              setLockedElements(prev => {
                const newLocks = { ...prev };
                delete newLocks[data.element_id];
                return newLocks;
              });
              break;
            case 'tareas_actualizadas':
              window.dispatchEvent(new Event('refetch_tareas_ia'));
              break;
            case 'diagram_event':
              window.dispatchEvent(new CustomEvent('remote_diagram_event', { detail: data.payload }));
              break;
          }
        } catch (e) {
          console.error("Error parsing WS message", e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting in 3 seconds...');
        reconnectTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, [codigo, isGuest, isOnline]);

  const approveGuest = (guestId: string, approved: boolean, proyectoId: number) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'admission_response',
        guest_id: guestId,
        approved,
        proyecto_id: proyectoId
      }));
      setPendingGuests(prev => prev.filter(g => g.guest_id !== guestId));
    }
  };

  const requestRoomUsers = () => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'get_room_users' }));
    }
  };
  
  const kickUser = (guestId: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'kick_user', guest_id: guestId }));
    }
  };
  
  const changeUserRole = (guestId: string, role: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'change_role', guest_id: guestId, role }));
    }
  };

  const broadcastDiagramEvent = (event: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'diagram_event',
        payload: event
      }));
    }
  };

  const broadcastDiagramDelta = (head: string, objects: Record<string, any>) => {
    if (sala.isOfflineMode || !navigator.onLine) {
      // Offline mode: guardamos directamente en la BD local IndexedDB
      import('@/features/gestion_concurrencia/sincronizar_estado_local/services/OfflineSyncService').then(({ offlineSyncService }) => {
        Object.keys(objects).forEach(hash => {
          offlineSyncService.putObject(hash, objects[hash]);
        });
      });
      return;
    }

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'diagram_delta',
        head,
        objects
      }));
    }
  };

  // Assign to window to avoid React hook circular deps with DiagramContext
  useEffect(() => {
    // @ts-ignore
    window.__broadcastDiagramDelta = broadcastDiagramDelta;
  }, [broadcastDiagramDelta]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        const identity = getUserIdentity();
        
        socketRef.current.send(JSON.stringify({
          type: 'mouse_move',
          user_id: identity.id,
          nickname: identity.nickname,
          x: e.clientX,
          y: e.clientY
        }));
      }
    };

    let timeout: any;
    const throttledMove = (e: MouseEvent) => {
      if (!timeout) {
        timeout = setTimeout(() => {
          handleMouseMove(e);
          timeout = null;
        }, 50); // 20fps
      }
    };

    window.addEventListener('mousemove', throttledMove);
    return () => {
      window.removeEventListener('mousemove', throttledMove);
      if (timeout) clearTimeout(timeout);
    };
  }, [isGuest]);

  const lockElement = (elementId: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'lock_element', element_id: elementId }));
    }
  };

  const refreshLock = (elementId: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'refresh_lock', element_id: elementId }));
    }
  };

  const unlockElement = (elementId: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'unlock_element', element_id: elementId }));
    }
  };

  return (
    <RealTimeSyncContext.Provider value={{
      socket: socketRef.current,
      pendingGuests,
      cursors,
      lockedElements,
      lockElement,
      refreshLock,
      unlockElement,
      approveGuest, broadcastDiagramEvent, broadcastDiagramDelta, roomUsers, requestRoomUsers, kickUser, changeUserRole, isReadOnly }}>
      {children}
    </RealTimeSyncContext.Provider>
  );
};

export const useRealTimeSync = () => {
  const context = useContext(RealTimeSyncContext);
  if (!context) throw new Error("useRealTimeSync must be used within RealTimeSyncProvider");
  return context;
};
