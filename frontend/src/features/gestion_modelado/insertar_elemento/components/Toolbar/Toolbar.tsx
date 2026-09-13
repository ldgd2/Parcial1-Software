import React, { useState } from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import { ChevronDown, ChevronRight, MousePointer2, GitCommit } from 'lucide-react';
import './Toolbar.css';

type ToolId = 'select' | 'connect' | NodeType;

interface Tool {
  id: ToolId;
  icon: React.ReactNode;
  label: string;
}

interface ToolGroup {
  name: string;
  tools: Tool[];
}

const ClassIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/></svg>;
const InterfaceIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/></svg>;
const AbstractIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/><path d="M9 16l3-8 3 8M10 13h4"/></svg>;
const EnumIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
const NoteIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>;
const PartIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><line x1="4" y1="10" x2="20" y2="10"/></svg>;
const PortIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="8" y="8" width="8" height="8"/></svg>;
const ExposeIcon = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4"/><path d="M16 12h5M3 12h5"/></svg>;

const ClassIconUML = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/><line x1="5" y1="8" x2="19" y2="8"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const DependencyIconUML = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12" strokeDasharray="4 4"/><polyline points="15 8 19 12 15 16"/></svg>;
const EventIconUML = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12,4 20,12 12,20 4,12" fill="purple"/></svg>;

const GROUPS: ToolGroup[] = [
  {
    name: 'General',
    tools: [
      { id: 'select',    icon: <MousePointer2 size={18} />, label: 'Seleccionar (Esc)' },
      { id: 'connect',   icon: <GitCommit size={18} />,     label: 'Conectar (C)' },
    ]
  },
  {
    name: 'UML Standard Profile',
    tools: [
      { id: 'auxillary' as any, icon: ClassIconUML, label: 'Auxillary' },
      { id: 'calls' as any, icon: DependencyIconUML, label: 'Call' },
      { id: 'create' as any, icon: DependencyIconUML, label: 'Create' },
      { id: 'create_event' as any, icon: EventIconUML, label: 'Create (Event)' },
      { id: 'destroy_event' as any, icon: EventIconUML, label: 'Destroy (Event)' },
      { id: 'focus' as any, icon: ClassIconUML, label: 'Focus' },
      { id: 'implementation_class' as any, icon: ClassIconUML, label: 'Implementation Class' },
      { id: 'instantiate' as any, icon: DependencyIconUML, label: 'Instantiate' },
      { id: 'realization_class' as any, icon: ClassIconUML, label: 'Realization' },
      { id: 'send' as any, icon: DependencyIconUML, label: 'Send' },
      { id: 'specification' as any, icon: ClassIconUML, label: 'Specification' },
      { id: 'type' as any, icon: ClassIconUML, label: 'Type' },
      { id: 'utility' as any, icon: ClassIconUML, label: 'Utility' }
    ]
  },
  {
    name: 'UML Structural',
    tools: [
      { id: 'class',     icon: ClassIcon,    label: 'Clase (Shift+C)' },
      { id: 'interface', icon: InterfaceIcon,label: 'Interfaz (Shift+I)' },
      { id: 'abstract',  icon: AbstractIcon, label: 'Clase Abstracta' },
      { id: 'enum',      icon: EnumIcon,     label: 'Enumeración (Shift+E)' },
      { id: 'note',      icon: NoteIcon,     label: 'Nota (Shift+N)' },
    ]
  },
  {
    name: 'Composite',
    tools: [
      { id: 'part',      icon: PartIcon,     label: 'Part' },
      { id: 'port',      icon: PortIcon,     label: 'Port' },
      { id: 'expose_interface', icon: ExposeIcon, label: 'Expose Interface' },
      { id: 'assembly' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M5 12h4M15 12h4"/><path d="M10 9a4 4 0 0 0 0 6" /></svg>, label: 'Assembly' },
      { id: 'connector' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>, label: 'Connector' },
      { id: 'delegate' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="15 8 19 12 15 16"/></svg>, label: 'Delegate' },
    ]
  },
  {
    name: 'Common',
    tools: [
      { id: 'artifact', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>, label: 'Artifact' },
      { id: 'requirement', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="5" width="18" height="14" rx="2" ry="2"/><path d="M9 10h6"/><path d="M9 14h6"/></svg>, label: 'Requirement' },
      { id: 'issue', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>, label: 'Issue' },
      { id: 'change', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 22 8.5 22 21.5 12 15 2 21.5 2 8.5 12 2"/></svg>, label: 'Change' },
      { id: 'information_item', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>, label: 'Information Item' },
      { id: 'constraint', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3"/><path d="M16 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3"/></svg>, label: 'Constraint' },
      { id: 'text', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>, label: 'Text Element' },
      { id: 'boundary', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>, label: 'Boundary' },
    ]
  },
  {
    name: 'Asociaciones',
    tools: [
      { id: 'association' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="15 8 19 12 15 16"/></svg>, label: 'Asociación' },
      { id: 'inheritance' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="16" y2="12"/><polygon points="16,8 16,16 21,12" fill="none" stroke="currentColor"/></svg>, label: 'Herencia' },
      { id: 'composition' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="15" y2="12"/><polygon points="15,12 18,9 21,12 18,15" fill="currentColor"/></svg>, label: 'Composición' },
      { id: 'aggregation' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="15" y2="12"/><polygon points="15,12 18,9 21,12 18,15" fill="none" stroke="currentColor"/></svg>, label: 'Agregación' },
      { id: 'association_class' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" y1="16" x2="14" y2="16"/><line x1="9" y1="16" x2="9" y2="7" strokeDasharray="3 3"/><rect x="6" y="4" width="6" height="4" fill="none"/></svg>, label: 'Association Class' },
      { id: 'dependency' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12" strokeDasharray="4 4"/><polyline points="15 8 19 12 15 16"/></svg>, label: 'Dependencia' },
      { id: 'realization' as any, icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="16" y2="12" strokeDasharray="4 4"/><polygon points="16,8 16,16 21,12" fill="none" stroke="currentColor"/></svg>, label: 'Realización' },
    ]
  }
];

export const Toolbar: React.FC = () => {
  const { addNode, cancelConnect, connectingSource, activeTool, setActiveTool } = useDiagram();
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['General', 'UML Standard Profile', 'UML Structural', 'Composite', 'Common', 'Asociaciones']);

  const toggleGroup = (name: string) => {
    setExpandedGroups(prev => 
      prev.includes(name) ? prev.filter(g => g !== name) : [...prev, name]
    );
  };

  const handleTool = (tool: Tool) => {
    const relationTools = ['association', 'inheritance', 'composition', 'aggregation', 'dependency', 'realization', 'directed', 'association_class', 'template_binding', 'instantiate', 'substitution', 'usage', 'trace', 'information_flow', 'abstraction', 'calls', 'delegate', 'assembly', 'create', 'send'];

    if (tool.id === 'select') {
      cancelConnect();
      setActiveTool('select');
    } else if (tool.id === 'connect' || relationTools.includes(tool.id as string)) {
      setActiveTool(tool.id as any);
    } else {
      cancelConnect();
      addNode(tool.id as NodeType);
      setActiveTool('select');
    }
  };

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === 'Escape') { cancelConnect(); setActiveTool('select'); }
      if (e.key === 'c' || e.key === 'C') { if (e.shiftKey) { addNode('class'); } else { setActiveTool('connect'); } }
      if (e.shiftKey && e.key === 'I') addNode('interface');
      if (e.shiftKey && e.key === 'E') addNode('enum');
      if (e.shiftKey && e.key === 'N') addNode('note');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [addNode, cancelConnect, setActiveTool]);

  return (
    <div className="toolbox-panel">
      <div className="toolbox-header">
        <span className="toolbox-title">Toolbox</span>
      </div>
      
      <div className="toolbox-content">
        {GROUPS.map(group => {
          const isExpanded = expandedGroups.includes(group.name);
          return (
            <div key={group.name} className="toolbox-group">
              <button 
                className="toolbox-group-header"
                onClick={() => toggleGroup(group.name)}
              >
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span>{group.name}</span>
              </button>
              
              {isExpanded && (
                <div className="toolbox-group-items">
                  {group.tools.map(t => {
                    const isActive = activeTool === t.id || (t.id === 'connect' && connectingSource);
                    return (
                      <button
                        key={t.id}
                        id={`tool-${t.id}`}
                        className={`toolbox-item ${isActive ? 'toolbox-item--active' : ''}`}
                        title={t.label}
                        onClick={() => handleTool(t)}
                      >
                        <span className="toolbox-item-icon">{t.icon}</span>
                        <span className="toolbox-item-label">{t.label}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="toolbox-footer">
        {connectingSource
          ? <span className="toolbox-status connecting">Clic en destino...</span>
          : <span className="toolbox-status idle">Modo: {activeTool}</span>
        }
      </div>
    </div>
  );
};
