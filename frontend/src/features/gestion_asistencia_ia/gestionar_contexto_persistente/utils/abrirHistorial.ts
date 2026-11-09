/**
 * Abrir el "Historial del proyecto" desde fuera del chat (p. ej. menú HERRAMIENTAS).
 * El modal vive dentro del panel del chat, que puede no estar montado todavía:
 * la petición queda pendiente hasta que el panel la recoge.
 */
export const EVENTO_ABRIR_HISTORIAL = 'historial:abrir';

let pendiente = false;

export function pedirAbrirHistorial(): void {
  pendiente = true;
  window.dispatchEvent(new Event(EVENTO_ABRIR_HISTORIAL));
}

/** Devuelve true (una sola vez) si alguien pidió abrir el historial. */
export function tomarPeticionHistorial(): boolean {
  const habia = pendiente;
  pendiente = false;
  return habia;
}
