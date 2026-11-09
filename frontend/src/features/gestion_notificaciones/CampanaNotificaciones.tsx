import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Sparkles, CheckCircle2, ClipboardList, UserPlus, DoorOpen, MessageSquare, Bell, type LucideIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { TokenService } from '@/shared/lib/TokenService';
import {
  EVENTO_NOTIFICACION,
  activarPush,
  configPush,
  listarNotificaciones,
  marcarLeida,
  marcarTodas,
  pushActivo,
  pushSoportado,
  reanudarPush,
  type ConfigPush,
  type Notificacion,
} from './notificaciones';
import './CampanaNotificaciones.css';

const ICONOS: Record<string, LucideIcon> = {
  propuesta_pendiente: Sparkles,
  propuesta_decidida: CheckCircle2,
  tarea_asignada: ClipboardList,
  solicitud_union: UserPlus,
  solicitud_aprobada: DoorOpen,
  comentario: MessageSquare,
};

const CADA_MS = 30_000;

function hace(iso: string | null) {
  if (!iso) return '';
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return 'ahora';
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return new Date(iso).toLocaleDateString('es', { day: '2-digit', month: 'short' });
}

/** CU39: campana con los avisos del usuario (dashboard y sala). */
export const CampanaNotificaciones: React.FC<{ className?: string }> = ({ className }) => {
  const navigate = useNavigate();
  const [abierta, setAbierta] = useState(false);
  const [items, setItems] = useState<Notificacion[]>([]);
  const [noLeidas, setNoLeidas] = useState(0);
  const [config, setConfig] = useState<ConfigPush | null>(null);
  const [push, setPush] = useState(pushActivo());
  const [errorPush, setErrorPush] = useState<string | null>(null);
  const [activando, setActivando] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const conSesion = !!TokenService.getToken();

  const cargar = useCallback(async () => {
    if (!TokenService.getToken()) return;
    try {
      const r = await listarNotificaciones();
      setItems(r.items);
      setNoLeidas(r.no_leidas);
    } catch { /* sin red: se reintenta en la próxima consulta */ }
  }, []);

  useEffect(() => {
    if (!conSesion) return;
    cargar();
    configPush().then(c => { setConfig(c); reanudarPush(c); }).catch(() => setConfig({ push: false }));
    const intervalo = window.setInterval(() => { if (document.visibilityState === 'visible') cargar(); }, CADA_MS);
    const alVolver = () => { if (document.visibilityState === 'visible') cargar(); };
    document.addEventListener('visibilitychange', alVolver);
    window.addEventListener(EVENTO_NOTIFICACION, cargar);
    return () => {
      window.clearInterval(intervalo);
      document.removeEventListener('visibilitychange', alVolver);
      window.removeEventListener(EVENTO_NOTIFICACION, cargar);
    };
  }, [cargar, conSesion]);

  useEffect(() => {
    if (!abierta) return;
    const fuera = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setAbierta(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setAbierta(false); };
    document.addEventListener('mousedown', fuera);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', fuera); document.removeEventListener('keydown', esc); };
  }, [abierta]);

  if (!conSesion) return null;

  const abrir = async (n: Notificacion) => {
    if (!n.leida) {
      setItems(prev => prev.map(i => (i.id === n.id ? { ...i, leida: true } : i)));
      setNoLeidas(c => Math.max(0, c - 1));
      marcarLeida(n.id).catch(() => {});
    }
    setAbierta(false);
    if (n.url && n.url !== window.location.pathname) navigate(n.url);
  };

  const leerTodas = async () => {
    setItems(prev => prev.map(i => ({ ...i, leida: true })));
    setNoLeidas(0);
    await marcarTodas().catch(() => {});
  };

  const activar = async () => {
    if (!config) return;
    setActivando(true);
    setErrorPush(null);
    try {
      await activarPush(config);
      setPush(true);
    } catch (e) {
      setErrorPush(e instanceof Error ? e.message : 'No se pudieron activar las notificaciones.');
    } finally {
      setActivando(false);
    }
  };

  return (
    <div className={`campana ${className ?? ''}`} ref={ref}>
      <button
        type="button"
        className="campana__boton"
        onClick={() => { setAbierta(a => !a); if (!abierta) cargar(); }}
        aria-label={noLeidas ? `Notificaciones: ${noLeidas} sin leer` : 'Notificaciones'}
        aria-expanded={abierta}
        title="Notificaciones"
      >
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {noLeidas > 0 && <span className="campana__badge">{noLeidas > 99 ? '99+' : noLeidas}</span>}
      </button>

      {abierta && (
        <div className="campana__panel" role="dialog" aria-label="Notificaciones">
          <header className="campana__cabecera">
            <span>Notificaciones</span>
            {noLeidas > 0 && <button type="button" onClick={leerTodas}>Marcar todas como leídas</button>}
          </header>

          {config?.push && pushSoportado() && !push && (
            <div className="campana__push">
              <span>Recibe avisos aunque la app esté cerrada.</span>
              <button type="button" onClick={activar} disabled={activando}>{activando ? 'Activando…' : 'Activar'}</button>
              {errorPush && <small role="alert">{errorPush}</small>}
            </div>
          )}

          {!items.length ? (
            <div className="campana__vacio">No tienes notificaciones.</div>
          ) : (
            <ul className="campana__lista">
              {items.map(n => (
                <li key={n.id}>
                  <button type="button" className={`campana__item${n.leida ? '' : ' is-nueva'}`} onClick={() => abrir(n)}>
                    <span className="campana__icono" aria-hidden="true">{React.createElement(ICONOS[n.tipo] ?? Bell, { size: 16 })}</span>
                    <span className="campana__texto">
                      <strong>{n.titulo}</strong>
                      {n.mensaje && <span>{n.mensaje}</span>}
                      <small>{hace(n.creada_en)}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
