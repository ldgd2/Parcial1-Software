/** CU39: servicio de notificaciones + registro opcional de push con Firebase Cloud Messaging. */
import { apiFetch } from '@/shared/lib/api';

export interface Notificacion {
  id: number;
  tipo: 'propuesta_pendiente' | 'propuesta_decidida' | 'tarea_asignada' | 'solicitud_union' | 'solicitud_aprobada' | 'comentario' | string;
  titulo: string;
  mensaje: string;
  url: string | null;
  proyecto_id: number | null;
  leida: boolean;
  creada_en: string | null;
}

export interface ConfigPush {
  push: boolean;
  vapidKey?: string;
  firebase?: Record<string, string>;
}

export const listarNotificaciones = () =>
  apiFetch<{ no_leidas: number; items: Notificacion[] }>('/api/notificaciones?limite=30');
export const marcarLeida = (id: number) => apiFetch(`/api/notificaciones/${id}/leer`, { method: 'POST' });
export const marcarTodas = () => apiFetch('/api/notificaciones/leer-todas', { method: 'POST' });
export const configPush = () => apiFetch<ConfigPush>('/api/notificaciones/config');

/** Evento interno: llegó un push con la pestaña abierta → refrescar la campana. */
export const EVENTO_NOTIFICACION = 'notificacion_recibida';

// SDK de Firebase desde su CDN oficial: solo se descarga si el push está configurado y el usuario lo activa.
const FIREBASE_VERSION = '10.12.2';
const CDN = `https://www.gstatic.com/firebasejs/${FIREBASE_VERSION}`;
const CLAVE_TOKEN = 'fcm_token';

export const pushSoportado = () =>
  typeof window !== 'undefined' && 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;

export const pushActivo = () => {
  try { return pushSoportado() && Notification.permission === 'granted' && !!localStorage.getItem(CLAVE_TOKEN); } catch { return false; }
};

async function cargarMessaging(config: ConfigPush) {
  const appMod: any = await import(/* @vite-ignore */ `${CDN}/firebase-app.js`);
  const msgMod: any = await import(/* @vite-ignore */ `${CDN}/firebase-messaging.js`);
  const app = appMod.getApps().length ? appMod.getApp() : appMod.initializeApp(config.firebase);
  return { messaging: msgMod.getMessaging(app), msgMod };
}

let escuchando = false;

/** Pide permiso, registra el service worker y guarda el token en el backend. */
export async function activarPush(config: ConfigPush): Promise<void> {
  if (!config.push || !config.firebase || !config.vapidKey) throw new Error('Las notificaciones push no están configuradas en el servidor.');
  if (!pushSoportado()) throw new Error('Este navegador no admite notificaciones push.');
  const permiso = await Notification.requestPermission();
  if (permiso !== 'granted') throw new Error('No diste permiso para mostrar notificaciones.');

  const sw = await navigator.serviceWorker.register(
    `/firebase-messaging-sw.js?v=${FIREBASE_VERSION}&config=${encodeURIComponent(JSON.stringify(config.firebase))}`,
  );
  const { messaging, msgMod } = await cargarMessaging(config);
  const token: string = await msgMod.getToken(messaging, { vapidKey: config.vapidKey, serviceWorkerRegistration: sw });
  if (!token) throw new Error('Firebase no devolvió un token para este navegador.');
  await apiFetch('/api/notificaciones/dispositivos', { method: 'POST', body: JSON.stringify({ token, plataforma: 'web' }) });
  try { localStorage.setItem(CLAVE_TOKEN, token); } catch { /* sin almacenamiento: igual queda registrado */ }
  escucharPrimerPlano(messaging, msgMod);
}

/** Con la pestaña abierta el navegador no muestra el push: avisamos a la campana. */
function escucharPrimerPlano(messaging: any, msgMod: any) {
  if (escuchando) return;
  escuchando = true;
  msgMod.onMessage(messaging, () => window.dispatchEvent(new Event(EVENTO_NOTIFICACION)));
}

/** Al recargar la página, si el push ya estaba activo, vuelve a escuchar en primer plano. */
export async function reanudarPush(config: ConfigPush) {
  if (!config.push || !pushActivo()) return;
  try {
    const { messaging, msgMod } = await cargarMessaging(config);
    escucharPrimerPlano(messaging, msgMod);
  } catch { /* sin red al CDN: la campana sigue funcionando por consulta periódica */ }
}

/** Al cerrar sesión: este navegador deja de recibir avisos de la cuenta. */
export async function desactivarPushLocal() {
  let token: string | null = null;
  try { token = localStorage.getItem(CLAVE_TOKEN); localStorage.removeItem(CLAVE_TOKEN); } catch { /* nada */ }
  if (token) await apiFetch(`/api/notificaciones/dispositivos?token=${encodeURIComponent(token)}`, { method: 'DELETE' }).catch(() => {});
}
