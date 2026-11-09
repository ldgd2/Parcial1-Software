import React from 'react';
import { X } from 'lucide-react';
import { AVAILABLE_COMMANDS } from './CommandList';

/** Usos del chat que no son comandos con "/" */
export const USOS_BASICOS = [
  { label: '@diag <pedido>', description: 'Pedir un cambio a la IA. Llega como propuesta: alguien con permiso de edición la aprueba o rechaza.', example: '@diag agrega email a Cliente' },
  { label: '@nombre', description: 'Mencionar a alguien de la sala.', example: '@Ana revisa la clase Pedido' },
];

/** Texto plano del resumen (lo usa /ayuda en el chat). Se arma desde la misma lista que el autocompletado. */
export function textoAyudaComandos(): string {
  const basicos = USOS_BASICOS.map(u => `• ${u.label} — ${u.description}\n   Ej.: ${u.example}`);
  const comandos = AVAILABLE_COMMANDS.map(c => `• ${c.label} — ${c.description}\n   Ej.: ${c.example}`);
  return ['Cómo usar el chat:', ...basicos, '', 'Comandos (escribe "/" para ver la lista):', ...comandos].join('\n');
}

interface Props {
  onCerrar: () => void;
}

/** Panel con el resumen de comandos; solo lo ve quien lo abre. */
export const AyudaComandos: React.FC<Props> = ({ onCerrar }) => (
  <div className="ayuda-comandos" role="dialog" aria-label="Comandos del chat">
    <div className="ayuda-comandos__head">
      <span>Cómo usar el chat</span>
      <button type="button" className="ayuda-comandos__cerrar" onClick={onCerrar} aria-label="Cerrar ayuda"><X size={14} aria-hidden="true" /></button>
    </div>
    <ul className="ayuda-comandos__lista">
      {[...USOS_BASICOS, ...AVAILABLE_COMMANDS].map(c => (
        <li key={c.label}>
          <code className="ayuda-comandos__cmd">{c.label}</code>
          <span className="ayuda-comandos__desc">{c.description}</span>
          <span className="ayuda-comandos__ej">Ej.: {c.example}</span>
        </li>
      ))}
    </ul>
    <p className="ayuda-comandos__nota">Los cambios de la IA nunca se aplican solos: siempre pasan por aprobación y quedan en el historial.</p>
  </div>
);
