import React from 'react';
import './ContextMenu.css';

export interface ContextMenuOption {
  label?: string;
  icon?: React.ReactNode;
  action: () => void;
  danger?: boolean;
  separator?: boolean;
}

interface Props {
  x: number;
  y: number;
  options: ContextMenuOption[];
  onClose: () => void;
}

export const ContextMenu: React.FC<Props> = ({ x, y, options, onClose }) => {
  // Prevent clicks from propagating and closing the menu prematurely if handled inside
  const handleClick = (e: React.MouseEvent, option: ContextMenuOption) => {
    e.stopPropagation();
    if (option.separator) return;
    option.action();
    onClose();
  };

  return (
    <>
      <div className="context-menu-backdrop" onClick={onClose} onContextMenu={(e) => { e.preventDefault(); onClose(); }} />
      <div 
        className="context-menu" 
        style={{ left: x, top: y }}
        onContextMenu={(e) => e.preventDefault()}
      >
        {options.map((opt, idx) => (
          opt.separator ? (
            <div key={`sep-${idx}`} className="context-menu__separator" />
          ) : (
            <button 
              key={idx} 
              className={`context-menu__item${opt.danger ? ' context-menu__item--danger' : ''}`}
              onClick={(e) => handleClick(e, opt)}
            >
              {opt.icon && <span className="context-menu__icon">{opt.icon}</span>}
              {opt.label}
            </button>
          )
        ))}
      </div>
    </>
  );
};
