import React, { useState } from 'react';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import { proyectoService } from '@/features/gestion_proyectos/shared/utils/proyectoService';
import type { Proyecto } from '@/features/gestion_proyectos/shared/utils/types';
import './CompartirModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  proyecto: Proyecto | null;
}

export const CompartirModal: React.FC<Props> = ({ isOpen, onClose, proyecto }) => {
  const [copiado, setCopiado] = useState(false);

  if (!proyecto) return null;
  const link = proyectoService.getLinkInvitacion(proyecto.codigo_acceso);

  const copiar = async () => {
    await navigator.clipboard.writeText(link);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="COMPARTIR PROYECTO" width="520px">
      <div className="compartir-modal">
        <p className="compartir-modal__desc">
          Comparte este enlace para que otros usuarios puedan unirse al diagrama.
        </p>

        <div className="compartir-modal__proyecto-name">
          <span className="compartir-modal__icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
          {proyecto.nombre}
        </div>

        <div className="compartir-modal__link-box">
          <input
            id="input-link-invitacion"
            className="compartir-modal__link-input"
            type="text"
            value={link}
            readOnly
            onClick={e => (e.target as HTMLInputElement).select()}
          />
          <button
            id="btn-copiar-link"
            className={`compartir-modal__copy-btn ${copiado ? 'compartir-modal__copy-btn--copiado' : ''}`}
            onClick={copiar}
          >
            {copiado ? <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polyline points="20 6 9 17 4 12"/></svg> COPIADO</> : 'COPIAR'}
          </button>
        </div>

        <div className="compartir-modal__info">
          <span className="compartir-modal__info-icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
          Cualquier persona con el enlace podrá solicitar unirse como colaborador.
        </div>
      </div>
    </Modal>
  );
};
