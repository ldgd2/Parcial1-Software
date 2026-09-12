import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { getGuestId, getGuestNickname } from '@/shared/utils/animalNames';
import { useSearchParams } from 'react-router-dom';

interface PendingGuest {
  guest_id: string;
  nickname: string;
}

interface Cursor {
  x: number;
  y: number;
  nickname: string;
}

interface SalaSocketContextType {
  socket: WebSocket | null;
  pendingGuests: PendingGuest[];
  cursors: Record<string, Cursor>;
  approveGuest: (guestId: string, approved: boolean, proyectoId: number) => void;
  broadcastDiagramEvent: (event: any) => void;
  broadcastDiagramDelta: (head: string, objects: Record<string, any>) => void;
  roomUsers: any[];
  requestRoomUsers: () => void;
  kickUser: (guestId: string) => void;
  changeUserRole: (guestId: string, role: string) => void;
  isReadOnly: boolean;
}

const SalaSocketContext = createContext<SalaSocketContextType | null>(null);

export const SalaSocketProvider: React.FC<{ children: React.ReactNode; sala: any }> = ({ children, sala }) => {
  const [pendingGuests, setPendingGuests] = useState<PendingGuest[]>([]);
  const [cursors, setCursors] = useState<Record<string, Cursor>>({});
  const [roomUsers, setRoomUsers] = useState<any[]>([]);
  const [isReadOnly, setIsReadOnly] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  
  const [searchParams] = useSearchParams();
  const isGuest = searchParams.get('guest') === 'true' || (sala.rol_proyecto && sala.rol_proyecto !== 'anfitrion');
  const codigo = searchParams.get('codigo') || sala.codigo_acceso;

  useEffect(() => {
    let wsUrl = `ws://localhost:8000/ws/salas/${codigo}`;
    
    if (isGuest) {
      let guestId = getGuestId();
      let nickname = getGuestNickname();
      
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          guestId = `auth_${user.id}`;
          nickname = user.nombre || user.email.split('@')[0];
        } catch (e) {}
      }
      
      wsUrl += `?user_type=guest&guest_id=${guestId}&nickname=${encodeURIComponent(nickname)}`;
    } else {
      wsUrl += `?user_type=host`;
    }

    let ws: WebSocket | null = null;
    let reconnectTimeout: any;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
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
              if (data.objects) {
                // Dynamic import para no romper si ObjectStore no está listo
                import('@/features/gestion_modelado/shared/store/ObjectStore').then(({ objectStore }) => {
                  Object.keys(data.objects).forEach(hash => {
                    objectStore.putObject(hash, data.objects[hash]);
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
  }, [codigo, isGuest]);

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
        let userId = 'host';
        let nickname = 'Anfitrión';
        
        const userStr = localStorage.getItem('user');
        if (userStr) {
          try {
            const user = JSON.parse(userStr);
            nickname = user.nombre || user.email.split('@')[0];
            if (!isGuest) {
              userId = `host_${user.id}`;
            }
          } catch (e) {}
        }

        if (isGuest) {
          userId = getGuestId();
          nickname = getGuestNickname();
          
          if (userStr) {
            try {
              const user = JSON.parse(userStr);
              userId = `auth_${user.id}`;
              nickname = user.nombre || user.email.split('@')[0];
            } catch (e) {}
          }
        }
        
        socketRef.current.send(JSON.stringify({
          type: 'mouse_move',
          user_id: userId,
          nickname: nickname,
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

  return (
    <SalaSocketContext.Provider value={{ socket: socketRef.current, pendingGuests, cursors, approveGuest, broadcastDiagramEvent, broadcastDiagramDelta, roomUsers, requestRoomUsers, kickUser, changeUserRole, isReadOnly }}>
      {children}
    </SalaSocketContext.Provider>
  );
};

export const useSalaSocket = () => {
  const context = useContext(SalaSocketContext);
  if (!context) throw new Error("useSalaSocket must be used within SalaSocketProvider");
  return context;
};
