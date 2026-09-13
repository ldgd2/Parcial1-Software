import React, { useState } from 'react';
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
  Route,
  Link,
  Milestone,
  RefreshCcw,
  Replace,
  MousePointer2,
  ListTree,
  PhoneCall,
  Activity
} from 'lucide-react';
import './ConnectPicker.css';

interface Props {
  x: number;
  y: number;
  onPick: (type: RelationType) => void;
  onCancel: () => void;
}

interface RelationGroup {
  name: string;
  options: { type: RelationType; icon: React.ReactNode; label: string }[];
}

const RELATION_GROUPS: RelationGroup[] = [
  {
    name: 'Class Relationships',
    options: [
      { type: 'aggregation_to_whole', icon: <Copy size={16} />,         label: 'Aggregation to Whole' },
      { type: 'association',          icon: <ArrowRight size={16} />,   label: 'Association' },
      { type: 'association_class',    icon: <Link size={16} />,         label: 'AssociationClass' },
      { type: 'calls',                icon: <PhoneCall size={16} />,    label: 'Calls' },
      { type: 'composition_to_whole', icon: <BoxSelect size={16} />,    label: 'Composition to Whole' },
      { type: 'inheritance',          icon: <Share2 size={16} />,       label: 'Generalization' },
      { type: 'instantiate',          icon: <RefreshCcw size={16} />,   label: 'Instantiates' },
      { type: 'substitution',         icon: <Replace size={16} />,      label: 'Substitution' },
      { type: 'template_binding',     icon: <Milestone size={16} />,    label: 'Template Binding' },
      { type: 'aggregation_to_part',  icon: <Copy size={16} />,         label: 'Aggregation to Part' },
      { type: 'called_by',            icon: <PhoneCall size={16} />,    label: 'Called by' },
      { type: 'composition_to_part',  icon: <BoxSelect size={16} />,    label: 'Composition to Part' },
      { type: 'instantiated_by',      icon: <RefreshCcw size={16} />,   label: 'Instantiated by' },
      { type: 'abstraction',          icon: <Workflow size={16} />,     label: 'Abstraction' },
      { type: 'dependency',           icon: <Unlink size={16} />,       label: 'Dependency' },
      { type: 'information_flow',     icon: <Activity size={16} />,     label: 'Information Flow' },
      { type: 'realization',          icon: <Workflow size={16} />,     label: 'Realization' },
      { type: 'usage',                icon: <MousePointer2 size={16} />, label: 'Usage' },
      { type: 'trace',                icon: <ListTree size={16} />,     label: 'Trace' },
      { type: 'directed',             icon: <CornerUpRight size={16} />,label: 'Directed Association' },
    ]
  },
  {
    name: 'Composite Parts',
    options: [
      { type: 'assembly',     icon: <Link size={16} />,        label: 'Assembly' },
      { type: 'connector',    icon: <ArrowRight size={16} />,  label: 'Connector' },
      { type: 'delegate',     icon: <Share2 size={16} />,      label: 'Delegate' },
    ]
  },
  {
    name: 'Database Relationships',
    options: [
      { type: '1:1',          icon: <Database size={16} />,     label: '1 to 1' },
      { type: '1:N',          icon: <Route size={16} />,        label: '1 to N' },
      { type: 'N:M',          icon: <GitCommitHorizontal size={16} />, label: 'N to M' },
      { type: '0..1:1',       icon: <Database size={16} />,     label: '0..1 to 1' },
      { type: '0..1:N',       icon: <Route size={16} />,        label: '0..1 to N' },
      { type: '0..N:1',       icon: <Route size={16} style={{transform: 'scaleX(-1)'}}/>, label: '0..N to 1' },
      { type: '0..N:M',       icon: <GitCommitHorizontal size={16} />, label: '0..N to M' },
    ]
  }
];

export const ConnectPicker: React.FC<Props> = ({ x, y, onPick, onCancel }) => {
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['Class Relationships']);

  const toggleGroup = (name: string) => {
    setExpandedGroups(prev => 
      prev.includes(name) ? prev.filter(g => g !== name) : [...prev, name]
    );
  };

  return (
    <>
      <div
        className="connect-picker__overlay"
        onClick={onCancel}
      />
      <div
        className="connect-picker"
        style={{ left: x, top: y, maxHeight: '350px', overflowY: 'auto' }}
      >
        <div className="connect-picker__title">Tipos de relación</div>
        
        {RELATION_GROUPS.map(group => {
          const isExpanded = expandedGroups.includes(group.name);
          return (
            <div key={group.name} className="connect-picker__group">
              <button 
                className="connect-picker__group-header"
                onClick={() => toggleGroup(group.name)}
                style={{ 
                  width: '100%', 
                  textAlign: 'left', 
                  fontWeight: 'bold', 
                  padding: '6px', 
                  backgroundColor: 'var(--bg-secondary)', 
                  border: 'none', 
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}
              >
                <span>{group.name}</span>
                <span>{isExpanded ? '▼' : '▶'}</span>
              </button>
              
              {isExpanded && (
                <div className="connect-picker__group-content">
                  {group.options.map(opt => (
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
              )}
            </div>
          );
        })}
      </div>
    </>
  );
};
