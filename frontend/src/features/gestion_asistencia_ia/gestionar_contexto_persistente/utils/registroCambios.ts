/**
 * Control compartido del registro de cambios manuales.
 *
 * La IA (chat @diag) y la restauración de versiones ya guardan su propia versión,
 * así que antes de aplicar sus cambios:
 *   1. cierran la ráfaga manual en curso (para no mezclar autorías), y
 *   2. pausan el registro manual unos segundos.
 * Si un cambio de la IA no pudo registrar su versión, se marca el origen para que
 * el registro manual lo guarde como "IA" en vez de "MANUAL".
 */

/** Evento que emite RealTimeSyncContext por cada cambio LOCAL del diagrama. */
export const EVENTO_CAMBIO_LOCAL = 'diagram_local_change';

export interface OrigenCambio {
  intent: string;   // 'IA', 'RESTAURAR', …
  cmd: string;      // descripción (p. ej. el pedido a la IA)
}

let pausadoHasta = 0;
let origenPendiente: { origen: OrigenCambio; vence: number } | null = null;
let cerrarRafaga: (() => void) | null = null;

/** Lo registra el hook de cambios manuales; devuelve la función para desregistrarlo. */
export function registrarCierreRafaga(fn: () => void): () => void {
  cerrarRafaga = fn;
  return () => { if (cerrarRafaga === fn) cerrarRafaga = null; };
}

/** Cierra la ráfaga en curso y no registra cambios locales durante `ms`. */
export function pausarRegistroManual(ms = 2500) {
  cerrarRafaga?.();
  pausadoHasta = Date.now() + ms;
}

export const registroManualPausado = () => Date.now() < pausadoHasta;

/** Los próximos cambios (dentro de `ms`) se registran con este origen en vez de MANUAL. */
export function marcarOrigenProximosCambios(origen: OrigenCambio, ms = 4000) {
  cerrarRafaga?.();
  origenPendiente = { origen, vence: Date.now() + ms };
}

export function tomarOrigenPendiente(): OrigenCambio | null {
  if (!origenPendiente || Date.now() > origenPendiente.vence) {
    origenPendiente = null;
    return null;
  }
  const o = origenPendiente.origen;
  origenPendiente = null;
  return o;
}

/** Se emite cuando termina una ráfaga de cambios o se aplica una propuesta (detail: {nodes, relations}). */
export const EVENTO_DIAGRAMA_ESTABLE = 'diagrama_estable';

export function avisarDiagramaEstable(estado: { nodes: any[]; relations: any[] }) {
  window.dispatchEvent(new CustomEvent(EVENTO_DIAGRAMA_ESTABLE, { detail: estado }));
}
