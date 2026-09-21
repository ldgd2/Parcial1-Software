import React, { useState } from 'react';
import type { Proyecto } from '@/features/gestion_proyectos/shared/utils/types';
import './ProyectoCard.css';

interface Props {
  proyecto: Proyecto;
  onAbrir: (p: Proyecto) => void;
  onEditar: (p: Proyecto) => void;
  onCompartir: (p: Proyecto) => void;
  onEliminar: (p: Proyecto) => void;
  onGestionarEquipo?: (p: Proyecto) => void;
}

export const ProyectoCard: React.FC<Props> = ({ proyecto, onAbrir, onEditar, onCompartir, onEliminar, onGestionarEquipo }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const fecha = new Date(proyecto.fecha_creacion).toLocaleDateString('es-ES', {
    day: '2-digit', month: 'short', year: 'numeric'
  });

  const colabs = proyecto.colaboradores?.filter(c => c.estado === 'aprobado').length ?? 0;

  return (
    <div
      className="proyecto-card"
      tabIndex={0}
      onKeyDown={e => { if (e.key === 'Enter') onAbrir(proyecto); }}
    >
      {/* Top accent bar */}
      <div className="proyecto-card__bar" />

      {/* Main click area */}
      <div className="proyecto-card__body" onClick={() => onAbrir(proyecto)}>
        <div className="proyecto-card__icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></div>
        <h3 className="proyecto-card__title">{proyecto.nombre}</h3>
        {proyecto.descripcion && (
          <p className="proyecto-card__desc">{proyecto.descripcion}</p>
        )}
      </div>

      {/* Footer */}
      <div className="proyecto-card__footer">
        <div className="proyecto-card__meta">
          <span className="proyecto-card__date">{fecha}</span>
          <span className="proyecto-card__colabs">
            {colabs} {colabs === 1 ? 'colaborador' : 'colaboradores'}
          </span>
        </div>

        <div className="proyecto-card__actions">
          <button
            className="proyecto-card__action-btn"
            title="Compartir enlace"
            onClick={e => { e.stopPropagation(); onCompartir(proyecto); }}
          >
            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
          </button>
          <div className="proyecto-card__menu-wrap">
            <button
              className="proyecto-card__action-btn"
              title="Mas opciones"
              onClick={e => { e.stopPropagation(); setMenuOpen(v => !v); }}
            >
              <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/></svg>
            </button>
            {menuOpen && (
              <div className="proyecto-card__dropdown" onMouseLeave={() => setMenuOpen(false)}>
                {onGestionarEquipo && (
                  <button onClick={e => { e.stopPropagation(); setMenuOpen(false); onGestionarEquipo(proyecto); }}>
                    GESTOR IA
                  </button>
                )}
                <button onClick={e => { e.stopPropagation(); setMenuOpen(false); onEditar(proyecto); }}>
                  EDITAR
                </button>
                <button
                  className="proyecto-card__dropdown-danger"
                  onClick={e => { e.stopPropagation(); setMenuOpen(false); onEliminar(proyecto); }}
                >
                  ELIMINAR
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
