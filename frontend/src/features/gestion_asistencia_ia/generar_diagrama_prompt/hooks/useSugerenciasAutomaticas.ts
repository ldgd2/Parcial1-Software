import { useEffect, useRef } from 'react';
import { useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { EVENTO_DIAGRAMA_ESTABLE } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/utils/registroCambios';
import { detectarProblemas } from '../services/sugerenciasService';
import type { ChatMessage, SugerenciaIA } from '../types/chatTypes';

/** Máximo un mensaje automático cada… */
const INTERVALO_MS = 2 * 60 * 1000;
const MAX_POR_MENSAJE = 3;
const MAX_CLAVES = 300;

export const claveAjusteSugerencias = (proyectoId: number) => `sugerencias_auto_${proyectoId}`;
export const sugerenciasAutoActivas = (proyectoId: number) => {
  try { return localStorage.getItem(claveAjusteSugerencias(proyectoId)) !== 'off'; } catch { return true; }
};
/** Avisa a la burbuja/encabezado del chat que cambió el interruptor */
export const EVENTO_AJUSTE_SUGERENCIAS = 'sugerencias_auto_cambio';

export function setSugerenciasAuto(proyectoId: number, activas: boolean) {
  try { localStorage.setItem(claveAjusteSugerencias(proyectoId), activas ? 'on' : 'off'); } catch { /* sin almacenamiento */ }
  window.dispatchEvent(new Event(EVENTO_AJUSTE_SUGERENCIAS));
}

const leerJSON = <T,>(clave: string, porDefecto: T): T => {
  try { return JSON.parse(localStorage.getItem(clave) || 'null') ?? porDefecto; } catch { return porDefecto; }
};

/** Claves ya dichas en el chat (por este cliente o por otros: se leen del historial). */
function clavesDichas(proyectoId: number, codigoAcceso?: string): Set<string> {
  const propias = leerJSON<string[]>(`sugerencias_dichas_${proyectoId}`, []);
  const historial = codigoAcceso ? leerJSON<ChatMessage[]>(`chat_history_${codigoAcceso}`, []) : [];
  const delChat = historial.flatMap(m => (m.sugerencias || []).map(s => s.clave));
  return new Set([...propias, ...delChat]);
}

function recordarClaves(proyectoId: number, claves: string[]) {
  const actuales = leerJSON<string[]>(`sugerencias_dichas_${proyectoId}`, []);
  const todas = Array.from(new Set([...actuales, ...claves])).slice(-MAX_CLAVES);
  try { localStorage.setItem(`sugerencias_dichas_${proyectoId}`, JSON.stringify(todas)); } catch { /* sin almacenamiento */ }
}

/** Mensaje de @diag con sugerencias; lo ve toda la sala. */
export function crearMensajeSugerencias(sugerencias: SugerenciaIA[], encabezado: string): ChatMessage {
  const lineas = sugerencias.map(s => `• ${s.texto}`).join('\n');
  return {
    id: `ai_sug_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    senderId: 'bot_diag',
    senderName: '@diag',
    senderColor: '#25D366',
    text: `${encabezado}\n${lineas}`,
    timestamp: Date.now(),
    isAi: true,
    aiStatus: 'success',
    sugerencias,
  };
}

/** Publica un mensaje del bot en el chat grupal (aunque el panel del chat esté cerrado). */
export function publicarEnChat(mensaje: ChatMessage, sendChatMessage: (m: any) => void, codigoAcceso?: string) {
  sendChatMessage(mensaje);                                                         // resto de la sala
  window.dispatchEvent(new CustomEvent('remote_chat_message', { detail: mensaje })); // chat abierto aquí
  if (codigoAcceso) {                                                               // chat cerrado aquí
    const clave = `chat_history_${codigoAcceso}`;
    const historial = leerJSON<ChatMessage[]>(clave, []);
    if (!historial.some(m => m.id === mensaje.id)) {
      try { localStorage.setItem(clave, JSON.stringify([...historial, mensaje].slice(-100))); } catch { /* sin almacenamiento */ }
    }
  }
}

/**
 * CU33 — Sugerencias de la IA en el chat mientras se diagrama.
 * Cuando quien edita termina una ráfaga de cambios (o se aplica una propuesta), se revisa
 * el diagrama con el detector (sin IA) y se publican en el chat solo los problemas NUEVOS,
 * como máximo un mensaje cada 2 minutos. Solo publica el cliente que hizo el cambio.
 */
export function useSugerenciasAutomaticas({
  proyectoId,
  codigoAcceso,
  habilitado,
}: {
  proyectoId?: number;
  codigoAcceso?: string;
  habilitado: boolean;
}) {
  const { sendChatMessage } = useRealTimeSync();
  const ultimoRef = useRef(0);
  const enCursoRef = useRef(false);
  const configRef = useRef({ proyectoId, codigoAcceso, habilitado, sendChatMessage });
  configRef.current = { proyectoId, codigoAcceso, habilitado, sendChatMessage };

  useEffect(() => {
    let espera: ReturnType<typeof setTimeout> | null = null;

    const revisar = async (estado: { nodes: any[]; relations: any[] }) => {
      const { proyectoId: pid, codigoAcceso: codigo, habilitado: on, sendChatMessage: enviar } = configRef.current;
      if (!on || !pid || pid <= 0 || !sugerenciasAutoActivas(pid)) return;
      if (enCursoRef.current || Date.now() - ultimoRef.current < INTERVALO_MS) return;
      enCursoRef.current = true;
      try {
        const encontradas = await detectarProblemas(estado.nodes, estado.relations);
        if (!encontradas?.length) return;
        const dichas = clavesDichas(pid, codigo);
        const nuevas = encontradas.filter(s => !dichas.has(s.clave)).slice(0, MAX_POR_MENSAJE);
        if (!nuevas.length) return;
        recordarClaves(pid, nuevas.map(s => s.clave));
        ultimoRef.current = Date.now();
        publicarEnChat(crearMensajeSugerencias(nuevas, 'Sugerencias sobre el diagrama:'), enviar, codigo);
      } finally {
        enCursoRef.current = false;
      }
    };

    const alEstabilizarse = (e: Event) => {
      const estado = (e as CustomEvent<{ nodes: any[]; relations: any[] }>).detail;
      if (!estado) return;
      if (espera) clearTimeout(espera);
      espera = setTimeout(() => revisar(estado), 1500);
    };

    window.addEventListener(EVENTO_DIAGRAMA_ESTABLE, alEstabilizarse);
    return () => {
      window.removeEventListener(EVENTO_DIAGRAMA_ESTABLE, alEstabilizarse);
      if (espera) clearTimeout(espera);
    };
  }, []);
}
