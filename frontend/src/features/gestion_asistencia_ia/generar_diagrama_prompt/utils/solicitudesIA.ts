/**
 * Pedidos a @diag que nacen fuera del chat (p. ej. "Solucionar con IA" en una corrección).
 * Se encolan, se abre el chat y el chat los envía como un mensaje normal.
 */

export interface CorreccionVinculada {
  nodoId: string;
  id: string;
  clase: string;
}

export interface SolicitudIA {
  texto: string;                    // se envía como "@diag <texto>"
  correccion?: CorreccionVinculada; // al aprobarse la propuesta, se marca resuelta
}

/** SalaView abre el chat al recibirlo; el chat vacía la cola */
export const EVENTO_SOLICITUD_IA = 'solicitud_ia_pendiente';

const cola: SolicitudIA[] = [];

export function pedirALaIA(solicitud: SolicitudIA) {
  cola.push(solicitud);
  window.dispatchEvent(new Event(EVENTO_SOLICITUD_IA));
}

export function tomarSolicitudes(): SolicitudIA[] {
  return cola.splice(0, cola.length);
}
