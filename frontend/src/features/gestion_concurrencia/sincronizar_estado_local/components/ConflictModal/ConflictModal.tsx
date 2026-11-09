import React from 'react';
import { useDiagram } from '../../../../gestion_modelado/shared/context/DiagramContext';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import './ConflictModal.css';

export const ConflictModal: React.FC = () => {
  const { conflicts, resolveConflict } = useDiagram();

  if (!conflicts || conflicts.length === 0) return null;

  return (
    // No se puede cerrar sin resolver: cada conflicto exige una decisión
    <Modal
      isOpen
      onClose={() => {}}
      dismissible={false}
      layer="top"
      width="600px"
      title={
        <>
          <svg className="conflict-modal__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Conflictos de sincronización
        </>
      }
    >
      <p className="conflict-modal__intro">
        Se encontraron diferencias entre tus cambios offline y el servidor. Elige qué versión conservar en cada caso.
      </p>

      <div className="conflict-modal__list">
        {conflicts.map((conflict, idx) => (
          <div key={`${conflict.nodeId}-${conflict.field}-${idx}`} className="conflict-item">
            <div className="conflict-item__title">{conflict.nodeName}</div>
            <div className="conflict-item__field">{conflict.field.replace(/:/g, ' › ')}</div>

            <div className="conflict-item__diff">
              <div className="conflict-diff-card local">
                <h4>TU VERSIÓN (LOCAL)</h4>
                <pre>{JSON.stringify(conflict.localValue, null, 2)}</pre>
              </div>
              <div className="conflict-diff-card server">
                <h4>VERSIÓN DEL SERVIDOR</h4>
                <pre>{JSON.stringify(conflict.serverValue, null, 2)}</pre>
              </div>
            </div>

            <div className="conflict-item__actions">
              <button
                type="button"
                className="modal-btn"
                onClick={() => resolveConflict(conflict.nodeId, conflict.field, false)}
              >
                Aceptar servidor
              </button>
              <button
                type="button"
                className="modal-btn modal-btn--primary"
                onClick={() => resolveConflict(conflict.nodeId, conflict.field, true)}
              >
                Conservar el mío
              </button>
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
};
