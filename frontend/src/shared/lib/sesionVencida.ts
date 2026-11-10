import { API_URL } from './api';
import { cerrarSesion } from './session';

/** Marca para que el login explique por qué volvió a pedir la contraseña. */
export const AVISO_SESION_VENCIDA = 'sesion_vencida';

/**
 * Sesión vencida en CUALQUIER llamada al backend.
 *
 * `apiFetch` ya lo detectaba, pero varias pantallas (exportar a GitHub, notificaciones, tareas,
 * comentarios…) usan `fetch` directo: con el token vencido recibían 401 en silencio y la app
 * parecía conectada mientras todo "cargaba y moría". Aquí se intercepta `fetch` una sola vez:
 * un 401 de nuestra API a una petición que llevaba token → se cierra la sesión y se va al login.
 */
export function instalarDetectorSesionVencida(): void {
  const fetchOriginal = window.fetch.bind(window);
  let redirigiendo = false;

  window.fetch = async (entrada: RequestInfo | URL, init?: RequestInit) => {
    const respuesta = await fetchOriginal(entrada, init);
    if (respuesta.status !== 401 || redirigiendo) return respuesta;

    const url = typeof entrada === 'string' ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
    if (!url.startsWith(API_URL)) return respuesta;
    // Un login con clave incorrecta también da 401, pero sin token: ese error lo muestra el login
    if (/\/usuarios\/(login|logout)/.test(url)) return respuesta;

    const cabeceras = new Headers(init?.headers ?? (entrada instanceof Request ? entrada.headers : undefined));
    if (!cabeceras.get('Authorization')) return respuesta;

    redirigiendo = true;
    cerrarSesion();
    try { sessionStorage.setItem(AVISO_SESION_VENCIDA, '1'); } catch { /* sin almacenamiento */ }
    if (window.location.pathname !== '/login') window.location.href = '/login';
    return respuesta;
  };
}
