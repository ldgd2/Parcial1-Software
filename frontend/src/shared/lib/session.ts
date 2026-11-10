import { TokenService } from './TokenService';

/**
 * Datos de la persona que inició sesión guardados en este navegador.
 * Se borran al salir para que quien use el equipo después no herede su
 * identidad, sus API keys ni sus conversaciones.
 *
 * No se borra el diagrama offline ('diagrama_local'): puede tener cambios
 * sin sincronizar y perderlos sería peor que conservarlos.
 */
const CLAVES_SESION = [
  'user',
  'usuario_nombre',
  'custom_gemini_key',
  'custom_openrouter_key',
  'custom_kimi_key',
  'lastDiagramId',
];
const PREFIJOS_SESION = ['chat_history_'];

/** Borra los datos del usuario (no el token). */
export function limpiarDatosDeSesion(): void {
  try {
    CLAVES_SESION.forEach(k => localStorage.removeItem(k));
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const k = localStorage.key(i);
      if (k && PREFIJOS_SESION.some(p => k.startsWith(p))) localStorage.removeItem(k);
    }
  } catch {
    /* almacenamiento no disponible: no hay nada que limpiar */
  }
}

/** Cierra la sesión en este navegador: token + datos del usuario. */
export function cerrarSesion(): void {
  TokenService.removeToken();
  limpiarDatosDeSesion();
}

/**
 * CU03: invalida el token también en el servidor y luego limpia este navegador.
 * Si no hay red se cierra igual en local (el token vencerá solo).
 */
export async function cerrarSesionEnServidor(): Promise<void> {
  const token = TokenService.getToken();
  if (token) {
    const api = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    await fetch(`${api}/usuarios/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => undefined);
  }
  cerrarSesion();
}
