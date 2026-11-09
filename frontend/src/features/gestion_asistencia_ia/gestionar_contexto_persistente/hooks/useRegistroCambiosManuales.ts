import { useCallback, useEffect, useRef } from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import type { EstadoDiagramaVersion } from '../types';
import { crearVersion } from '../services/contextoService';
import { compararVersiones, type ComparacionVersiones } from '../utils/versionDiff';
import {
  EVENTO_CAMBIO_LOCAL,
  registrarCierreRafaga,
  registroManualPausado,
  tomarOrigenPendiente,
  avisarDiagramaEstable,
  type OrigenCambio,
} from '../utils/registroCambios';
import { EVENTO_VERSIONES_ACTUALIZADAS } from './useVersionesContexto';

/** Se cierra la ráfaga tras este tiempo sin editar… */
const ESPERA_MS = 4000;
/** …o, como máximo, este tiempo desde la primera edición. */
const MAXIMO_MS = 30000;

interface Rafaga {
  antes: EstadoDiagramaVersion;
  inicio: number;
  origen: OrigenCambio | null;
}

const lista = (xs: string[], max = 3) =>
  xs.length <= max ? xs.join(', ') : `${xs.slice(0, max).join(', ')} y ${xs.length - max} más`;

/** "Creó Pedido; editó Cliente (+ email); eliminó Factura; 1 relación nueva" */
function describir(c: ComparacionVersiones): string {
  const creadas = c.nodos.filter(n => n.estado === 'agregado').map(n => n.nombre);
  const editadas = c.nodos.filter(n => n.estado === 'modificado');
  const borradas = c.nodos.filter(n => n.estado === 'eliminado').map(n => n.nombre);
  const partes: string[] = [];
  if (creadas.length) partes.push(`Creó ${lista(creadas)}`);
  if (editadas.length) {
    const detalle = editadas.length === 1
      ? (() => {
          const n = editadas[0];
          const cambios = [
            ...n.atributos.agregados.map(a => `+ ${a.replace(/^\S+\s/, '')}`),
            ...n.atributos.eliminados.map(a => `− ${a.replace(/^\S+\s/, '')}`),
            ...n.metodos.agregados.map(m => `+ ${m.replace(/^\S+\s/, '')}`),
            ...n.metodos.eliminados.map(m => `− ${m.replace(/^\S+\s/, '')}`),
          ];
          const ren = n.renombradoDe ? `${n.renombradoDe} → ${n.nombre}` : n.nombre;
          return cambios.length ? `${ren} (${lista(cambios, 2)})` : ren;
        })()
      : lista(editadas.map(n => n.nombre));
    partes.push(`editó ${detalle}`);
  }
  if (borradas.length) partes.push(`eliminó ${lista(borradas)}`);
  const relN = c.relacionesAgregadas.length;
  const relE = c.relacionesEliminadas.length;
  if (relN) partes.push(`${relN} relación${relN > 1 ? 'es' : ''} nueva${relN > 1 ? 's' : ''}`);
  if (relE) partes.push(`${relE} relación${relE > 1 ? 'es' : ''} eliminada${relE > 1 ? 's' : ''}`);
  const texto = partes.join('; ') || 'Cambios en la pizarra';
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** Mismo formato que el delta de la IA: "+A,B | ~C | -D" */
function delta(c: ComparacionVersiones): string {
  const de = (e: string) => c.nodos.filter(n => n.estado === e).map(n => n.nombre).slice(0, 5).join(',');
  return [['+', de('agregado')], ['~', de('modificado')], ['-', de('eliminado')]]
    .filter(([, v]) => v)
    .map(([s, v]) => `${s}${v}`)
    .join(' | ');
}

/**
 * Registra en el historial los cambios que la persona hace a mano en la pizarra.
 * Agrupa ediciones seguidas en una sola versión (con su "antes" y "después").
 * Solo se registran los cambios locales: cada cliente guarda los suyos, sin duplicados.
 * Mover clases sin cambiar nada más no genera versión.
 */
export function useRegistroCambiosManuales({
  proyectoId,
  autor,
  habilitado,
}: {
  proyectoId?: number;
  autor?: string;
  habilitado: boolean;
}) {
  const { nodes, relations } = useDiagram();
  const estadoRef = useRef<EstadoDiagramaVersion>({ nodes, relations });
  estadoRef.current = { nodes, relations };

  // Último estado "estable": el "antes" de la próxima ráfaga
  const baseRef = useRef<EstadoDiagramaVersion | null>(null);
  const rafagaRef = useRef<Rafaga | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const configRef = useRef({ proyectoId, autor, habilitado });
  configRef.current = { proyectoId, autor, habilitado };

  // Sin ráfaga activa, la base sigue a la pizarra (incluye la carga inicial y los cambios remotos)
  useEffect(() => {
    if (!rafagaRef.current) baseRef.current = { nodes, relations };
  }, [nodes, relations]);

  const cerrar = useCallback((keepalive = false) => {
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; }
    const r = rafagaRef.current;
    rafagaRef.current = null;
    if (!r) return;

    const despues = estadoRef.current;
    baseRef.current = despues;
    const { proyectoId: pid, autor: quien } = configRef.current;
    if (!pid || pid <= 0) return;

    const cmp = compararVersiones(r.antes, despues);
    if (cmp.sinCambios) return;   // p. ej. solo se movieron clases
    if (!keepalive) avisarDiagramaEstable(despues);   // revisar y sugerir en el chat (CU33)

    const descripcion = describir(cmp);
    crearVersion(pid, {
      intent: r.origen?.intent ?? 'MANUAL',
      cmd: r.origen?.cmd ?? descripcion,
      resumen: descripcion,
      delta: delta(cmp),
      autor: quien ?? null,
      estado_antes: r.antes,
      estado_despues: despues,
    }, keepalive)
      .then(v => window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: { versionId: v.id } })))
      .catch(err => console.warn('[RegistroCambios] No se pudo guardar el cambio manual:', err));
  }, []);

  // Cada cambio local abre o extiende la ráfaga
  useEffect(() => {
    const alCambiar = () => {
      if (!configRef.current.habilitado || registroManualPausado()) return;
      const ahora = Date.now();
      if (!rafagaRef.current) {
        rafagaRef.current = {
          antes: baseRef.current ?? estadoRef.current,
          inicio: ahora,
          origen: tomarOrigenPendiente(),
        };
      }
      if (timerRef.current) clearTimeout(timerRef.current);
      const restante = MAXIMO_MS - (ahora - rafagaRef.current.inicio);
      // Pequeña espera mínima para que React aplique el último cambio antes de leer el "después"
      timerRef.current = setTimeout(() => cerrar(), Math.max(150, Math.min(ESPERA_MS, restante)));
    };
    window.addEventListener(EVENTO_CAMBIO_LOCAL, alCambiar);
    const desregistrar = registrarCierreRafaga(() => cerrar());
    return () => {
      window.removeEventListener(EVENTO_CAMBIO_LOCAL, alCambiar);
      desregistrar();
    };
  }, [cerrar]);

  // Al salir de la sala o cerrar la pestaña, guardar lo pendiente
  useEffect(() => {
    const alOcultar = () => { if (document.visibilityState === 'hidden') cerrar(true); };
    const alSalir = () => cerrar(true);
    document.addEventListener('visibilitychange', alOcultar);
    window.addEventListener('pagehide', alSalir);
    return () => {
      document.removeEventListener('visibilitychange', alOcultar);
      window.removeEventListener('pagehide', alSalir);
      cerrar(true);
    };
  }, [cerrar]);
}
