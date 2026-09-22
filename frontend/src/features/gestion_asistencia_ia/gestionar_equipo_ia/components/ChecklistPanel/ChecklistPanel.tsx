import React from 'react';
import type { TareaIA } from '../../services/equipoService';
import { useChecklistPanel } from '../../hooks/useChecklistPanel';
import './ChecklistPanel.css';

interface Props {
  proyectoId: number;
  isHost?: boolean;
  isChatOpen?: boolean;
  onOpenGestor?: () => void;
}

export const ChecklistPanel: React.FC<Props> = ({ proyectoId, isHost, isChatOpen, onOpenGestor }) => {
  const { tareas, loading, open, setOpen, toggleTarea, completadas, porcentaje } =
    useChecklistPanel(proyectoId);

  const tareasDiagrama = tareas.filter((t: TareaIA) => t.tipo === 'diagrama');
  const tareasDesarrollo = tareas.filter((t: TareaIA) => t.tipo === 'desarrollo');

  return (
    <div className={`checklist-panel ${open ? 'checklist-panel--open' : ''} ${isChatOpen ? 'checklist-panel--shifted' : ''}`}>
      <button
        id="btn-toggle-checklist"
        className="checklist-panel__trigger"
        onClick={() => setOpen((prev: boolean) => !prev)}
        title="Mis Tareas IA"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
        </svg>
        {completadas < tareas.length && (
          <span className="checklist-panel__badge">{tareas.length - completadas}</span>
        )}
      </button>

      {open && (
        <div className="checklist-panel__drawer">
          <div className="checklist-panel__header">
            <span className="checklist-panel__title">MIS TAREAS</span>
            <button className="checklist-panel__close" onClick={() => setOpen(false)}>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div className="checklist-panel__progress-bar-wrap">
            <div className="checklist-panel__progress-bar" style={{ width: `${porcentaje}%` }} />
          </div>
          <span className="checklist-panel__progress-label">
            {completadas} / {tareas.length} completadas ({porcentaje}%)
          </span>

          {loading && <div className="checklist-panel__loading">Cargando...</div>}

          {tareasDiagrama.length > 0 && (
            <div className="checklist-panel__section">
              <span className="checklist-panel__section-label">EN EL DIAGRAMADOR</span>
              {tareasDiagrama.map((t: TareaIA) => (
                <TareaItem key={t.id} tarea={t} onToggle={toggleTarea} />
              ))}
            </div>
          )}

          {tareasDesarrollo.length > 0 && (
            <div className="checklist-panel__section">
              <span className="checklist-panel__section-label">DESARROLLO EXTERNO</span>
              {tareasDesarrollo.map((t: TareaIA) => (
                <TareaItem key={t.id} tarea={t} onToggle={toggleTarea} />
              ))}
            </div>
          )}

          {!loading && tareas.length === 0 && (
            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              No tienes tareas asignadas.
            </div>
          )}

          {isHost && (
            <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', marginTop: '0.5rem' }}>
              <button
                onClick={onOpenGestor}
                style={{
                  width: '100%',
                  padding: '8px',
                  background: 'var(--primary)',
                  color: 'var(--bg-color)',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  textTransform: 'uppercase'
                }}
              >
                Gestor Equipo IA
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface TareaItemProps {
  tarea: TareaIA;
  onToggle: (id: number, v: boolean) => void;
}

const TareaItem: React.FC<TareaItemProps> = ({ tarea, onToggle }) => (
  <div
    className={`checklist-item ${tarea.completada ? 'checklist-item--done' : ''}`}
    onClick={() => onToggle(tarea.id, !tarea.completada)}
    id={`tarea-${tarea.id}`}
    role="checkbox"
    aria-checked={tarea.completada}
    tabIndex={0}
    onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && onToggle(tarea.id, !tarea.completada)}
  >
    <div className="checklist-item__checkbox">
      {tarea.completada && (
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="3">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      )}
    </div>
    <div className="checklist-item__body">
      <span className="checklist-item__titulo">{tarea.titulo}</span>
      {tarea.descripcion && (
        <span className="checklist-item__desc">{tarea.descripcion}</span>
      )}
    </div>
  </div>
);
