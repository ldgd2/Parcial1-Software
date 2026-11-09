import React, { useEffect, useId, useRef } from 'react';
import './Modal.css';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Texto o nodo (p. ej. icono + texto). Se muestra en mayúsculas. */
  title: React.ReactNode;
  children: React.ReactNode;
  width?: string;
  /** Botones de acción fijos al pie (no se desplazan con el contenido). */
  footer?: React.ReactNode;
  /** Acciones extra en la cabecera, a la izquierda del botón de cerrar. */
  headerActions?: React.ReactNode;
  /** false = no se cierra con Escape, clic fuera ni botón (decisión obligatoria). */
  dismissible?: boolean;
  /** Capa: 'modal' (por defecto) o 'top' para modales que deben quedar sobre otros. */
  layer?: 'modal' | 'top';
  /** Clases extra para el panel y el cuerpo (p. ej. cuerpo sin padding). */
  className?: string;
  bodyClassName?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  width = '480px',
  footer,
  headerActions,
  dismissible = true,
  layer = 'modal',
  className = '',
  bodyClassName = '',
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  useEffect(() => {
    if (!isOpen || !dismissible) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, dismissible, onClose]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className={`modal-overlay${layer === 'top' ? ' modal-overlay--top' : ''}`}
      ref={overlayRef}
      onClick={(e) => { if (dismissible && e.target === overlayRef.current) onClose(); }}
    >
      <div
        className={`modal-panel ${className}`.trim()}
        style={{ maxWidth: width }}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <div className="modal-header">
          <h2 className="modal-title" id={titleId}>{title}</h2>
          <div className="modal-header-actions">
            {headerActions}
            {dismissible && (
              <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
            )}
          </div>
        </div>
        <div className={`modal-body ${bodyClassName}`.trim()}>{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};
