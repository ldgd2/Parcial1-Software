import React from 'react';
import { useDiagram } from '../../../../gestion_modelado/shared/context/DiagramContext';
import './ConflictModal.css';

export const ConflictModal: React.FC = () => {
  const { conflicts, resolveConflict } = useDiagram();

  if (!conflicts || conflicts.length === 0) return null;

  return (
    <div className="conflict-modal-overlay">
      <div className="conflict-modal">
        <div className="conflict-modal__header">
          <h2>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Conflictos de Sincronización
          </h2>
          <p>Se encontraron diferencias entre tus cambios offline y el servidor. Por favor resuelve los conflictos.</p>
        </div>

        <div className="conflict-modal__body">
          {conflicts.map((conflict, idx) => (
            <div key={`${conflict.nodeId}-${conflict.field}-${idx}`} className="conflict-item">
              <div className="conflict-item__title">Elemento: {conflict.nodeName}</div>
              <div className="conflict-item__field">Campo: {conflict.field.replace(/:/g, ' > ')}</div>
              
              <div className="conflict-item__diff">
                <div className="conflict-diff-card local">
                  <h4>Tu versión (Local)</h4>
                  <pre>{JSON.stringify(conflict.localValue, null, 2)}</pre>
                </div>
                <div className="conflict-diff-card server">
                  <h4>Versión Servidor</h4>
                  <pre>{JSON.stringify(conflict.serverValue, null, 2)}</pre>
                </div>
              </div>

              <div className="conflict-item__actions">
                <button 
                  className="conflict-btn server-btn"
                  onClick={() => resolveConflict(conflict.nodeId, conflict.field, false)}
                >
                  Aceptar Servidor
                </button>
                <button 
                  className="conflict-btn local-btn"
                  onClick={() => resolveConflict(conflict.nodeId, conflict.field, true)}
                >
                  Conservar el mío
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
