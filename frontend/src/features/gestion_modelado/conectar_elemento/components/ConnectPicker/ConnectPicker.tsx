import React from 'react';
import type { RelationType } from '@/features/gestion_modelado/shared/types/types';
import { 
  ArrowRight, 
  CornerUpRight, 
  Share2, 
  Workflow, 
  BoxSelect, 
  Copy, 
  GitCommitHorizontal, 
  Database,
  Unlink,
  Route
} from 'lucide-react';
import './ConnectPicker.css';

interface Props {
  x: number;
  y: number;
  onPick: (type: RelationType) => void;
  onCancel: () => void;
}

const RELATION_OPTIONS: { type: RelationType; icon: React.ReactNode; label: string }[] = [
  { type: 'association',  icon: <ArrowRight size={16} />,   label: 'Asociación' },
  { type: 'directed',     icon: <CornerUpRight size={16} />,label: 'Asoc. Dirigida' },
  { type: 'inheritance',  icon: <Share2 size={16} />,       label: 'Herencia' },
  { type: 'realization',  icon: <Workflow size={16} />,     label: 'Realización' },
  { type: 'composition',  icon: <BoxSelect size={16} />,    label: 'Composición' },
  { type: 'aggregation',  icon: <Copy size={16} />,         label: 'Agregación' },
  { type: 'dependency',   icon: <Unlink size={16} />,       label: 'Dependencia' },
  { type: '1:1',          icon: <Database size={16} />,     label: 'BD: 1 a 1' },
  { type: '1:N',          icon: <Route size={16} />,        label: 'BD: 1 a N' },
  { type: 'N:M',          icon: <GitCommitHorizontal size={16} />, label: 'BD: N a M' },
  { type: '0..1:1',       icon: <Database size={16} />,     label: 'BD: 0..1 a 1' },
  { type: '0..1:N',       icon: <Route size={16} />,        label: 'BD: 0..1 a N' },
  { type: '0..N:1',       icon: <Route size={16} style={{transform: 'scaleX(-1)'}}/>, label: 'BD: 0..N a 1' },
  { type: '0..N:M',       icon: <GitCommitHorizontal size={16} />, label: 'BD: 0..N a M' },
];

export const ConnectPicker: React.FC<Props> = ({ x, y, onPick, onCancel }) => {
  return (
    <>
      {/* Overlay invisible para cancelar haciendo clic fuera */}
      <div
        className="connect-picker__overlay"
        onClick={onCancel}
      />
      <div
        className="connect-picker"
        style={{ left: x, top: y }}
      >
        <div className="connect-picker__title">Tipo de relación</div>
        {RELATION_OPTIONS.map(opt => (
          <button
            key={opt.type}
            id={`relation-${opt.type}`}
            className="connect-picker__option"
            onClick={() => onPick(opt.type)}
          >
            <span className="connect-picker__icon">{opt.icon}</span>
            <span>{opt.label}</span>
          </button>
        ))}
      </div>
    </>
  );
};
