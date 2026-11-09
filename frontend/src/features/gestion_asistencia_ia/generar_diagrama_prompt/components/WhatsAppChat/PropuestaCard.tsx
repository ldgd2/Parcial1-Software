import React, { useState } from 'react';
import type { PropuestaIA } from '../../types/chatTypes';

interface Props {
  propuesta: PropuestaIA;
  puedeDecidir: boolean;
  onDecidir?: (aceptar: boolean) => Promise<void>;
  onVerCambios?: () => void;
}

const hora = (ms?: number) =>
  ms ? new Date(ms).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

/** Cambios de la IA pendientes de aprobación, dentro de la burbuja del chat. */
export const PropuestaCard: React.FC<Props> = ({ propuesta: p, puedeDecidir, onDecidir, onVerCambios }) => {
  const [enviando, setEnviando] = useState<null | 'aprobar' | 'rechazar'>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandida, setExpandida] = useState(false);

  const decidir = async (aceptar: boolean) => {
    if (!onDecidir) return;
    setEnviando(aceptar ? 'aprobar' : 'rechazar');
    setError(null);
    try {
      await onDecidir(aceptar);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo completar la acción');
    } finally {
      setEnviando(null);
    }
  };

  const chips = [
    ...p.agregadas.map(n => ({ t: 'add', s: `+ ${n}` })),
    ...p.modificadas.map(n => ({ t: 'mod', s: `~ ${n}` })),
    ...p.eliminadas.map(n => ({ t: 'del', s: `− ${n}` })),
  ];

  // Plegado: se muestra un resumen y el resto bajo "Ver más"
  const LIM_CHIPS = 6;
  const LIM_LINEAS = 4;
  const lineas = p.lineas ?? [];
  const hayMas = chips.length > LIM_CHIPS || lineas.length > LIM_LINEAS;
  const chipsVisibles = expandida ? chips : chips.slice(0, LIM_CHIPS);
  const lineasVisibles = expandida ? lineas : lineas.slice(0, LIM_LINEAS);
  const ocultos = Math.max(0, chips.length - LIM_CHIPS) + Math.max(0, lineas.length - LIM_LINEAS);

  return (
    <div className={`propuesta-card propuesta-card--${p.estado}`}>
      <div className="propuesta-card__head">
        <span className="propuesta-card__titulo">
          {p.tipo === 'roles' ? 'Propuesta de roles' : p.tipo === 'tareas' ? 'Propuesta de tareas' : 'Propuesta de cambios'}
        </span>
        <span className={`propuesta-card__estado propuesta-card__estado--${p.estado}`}>
          {p.estado === 'pendiente' ? 'Pendiente' : p.estado === 'aprobada' ? 'Aprobada' : 'Rechazada'}
        </span>
      </div>

      {chips.length > 0 && (
        <div className="propuesta-card__chips">
          {chipsVisibles.map((c, i) => (
            <span key={i} className={`propuesta-card__chip propuesta-card__chip--${c.t}`}>{c.s}</span>
          ))}
        </div>
      )}
      {lineasVisibles.length > 0 && (
        <ul className="propuesta-card__lineas">
          {lineasVisibles.map((l, i) => <li key={i}>{l}</li>)}
        </ul>
      )}
      {hayMas && (
        <button
          type="button"
          className="propuesta-card__mas"
          onClick={() => setExpandida(v => !v)}
          aria-expanded={expandida}
        >
          {expandida ? "Ver menos ▴" : `Ver ${ocultos} más ▾`}
        </button>
      )}
      {(p.tareas ?? 0) > 0 && p.tipo !== 'tareas' && (
        <div className="propuesta-card__meta">Incluye {p.tareas} tarea{(p.tareas ?? 0) > 1 ? 's' : ''} para el equipo</div>
      )}
      {p.relaciones > 0 && (
        <div className="propuesta-card__meta">{p.relaciones} relación{p.relaciones > 1 ? 'es' : ''} en la propuesta</div>
      )}

      <div className="propuesta-card__meta">Pedida por {p.solicitadaPor}</div>
      {p.estado !== 'pendiente' && (
        <div className="propuesta-card__meta propuesta-card__meta--decision">
          {p.estado === 'aprobada' ? 'Aprobada' : 'Rechazada'} por {p.decididaPor || 'alguien de la sala'}
          {p.decididaEn ? ` · ${hora(p.decididaEn)}` : ''}
        </div>
      )}

      {error && <div className="propuesta-card__error" role="alert">{error}</div>}

      {p.estado === 'pendiente' && (puedeDecidir ? (
        <div className="propuesta-card__acciones">
          <>
            <button
              type="button"
              className="propuesta-card__btn propuesta-card__btn--rechazar"
              onClick={() => decidir(false)}
              disabled={!!enviando}
            >
              {enviando === 'rechazar' ? 'Rechazando…' : 'Rechazar'}
            </button>
            <button
              type="button"
              className="propuesta-card__btn propuesta-card__btn--aprobar"
              onClick={() => decidir(true)}
              disabled={!!enviando}
            >
              {enviando === 'aprobar' ? 'Aplicando…' : 'Aprobar'}
            </button>
          </>
        </div>
      ) : (
        <div className="propuesta-card__meta propuesta-card__espera">Esperando aprobación de alguien con permiso de edición</div>
      ))}

      {onVerCambios && (
        <button type="button" className="propuesta-card__link" onClick={onVerCambios}>
          Ver en historial →
        </button>
      )}
    </div>
  );
};
