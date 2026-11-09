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
          {chips.slice(0, 8).map((c, i) => (
            <span key={i} className={`propuesta-card__chip propuesta-card__chip--${c.t}`}>{c.s}</span>
          ))}
          {chips.length > 8 && <span className="propuesta-card__chip">+{chips.length - 8} más</span>}
        </div>
      )}
      {p.lineas && p.lineas.length > 0 && (
        <ul className="propuesta-card__lineas">
          {p.lineas.slice(0, 8).map((l, i) => <li key={i}>{l}</li>)}
          {p.lineas.length > 8 && <li>… y {p.lineas.length - 8} más</li>}
        </ul>
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

      <div className="propuesta-card__acciones">
        {onVerCambios && (
          <button type="button" className="propuesta-card__btn" onClick={onVerCambios}>
            Ver en historial
          </button>
        )}
        {p.estado === 'pendiente' && (puedeDecidir ? (
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
        ) : (
          <span className="propuesta-card__meta">Esperando aprobación de alguien con permiso de edición</span>
        ))}
      </div>
    </div>
  );
};
