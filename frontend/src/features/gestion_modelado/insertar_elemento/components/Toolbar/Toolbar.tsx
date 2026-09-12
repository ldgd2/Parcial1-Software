import React from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import './Toolbar.css';

type ToolId = 'select' | 'connect' | NodeType;

interface Tool {
  id: ToolId;
  icon: React.ReactNode;
  label: string;
  group: 'tools' | 'elements';
}

const SelectIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>;
const ConnectIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 19L19 5M19 5v8M19 5h-8"/></svg>;
const ClassIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/></svg>;
const InterfaceIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/></svg>;
const AbstractIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/><path d="M9 16l3-8 3 8M10 13h4"/></svg>;
const EnumIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
const NoteIcon = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>;

const TOOLS: Tool[] = [
  // ── Herramientas ──
  { id: 'select',    icon: SelectIcon,   label: 'Seleccionar (Esc)',      group: 'tools' },
  { id: 'connect',   icon: ConnectIcon,  label: 'Conectar (C)',           group: 'tools' },
  // ── CU8: Elementos ──
  { id: 'class',     icon: ClassIcon,    label: 'Clase (Shift+C)',        group: 'elements' },
  { id: 'interface', icon: InterfaceIcon,label: 'Interfaz (Shift+I)',     group: 'elements' },
  { id: 'abstract',  icon: AbstractIcon, label: 'Clase Abstracta',       group: 'elements' },
  { id: 'enum',      icon: EnumIcon,     label: 'Enumeración (Shift+E)', group: 'elements' },
  { id: 'note',      icon: NoteIcon,     label: 'Nota (Shift+N)',         group: 'elements' },
];

export const Toolbar: React.FC = () => {
  const { addNode, cancelConnect, connectingSource, activeTool, setActiveTool } = useDiagram();

  const handleTool = (tool: Tool) => {
    if (tool.id === 'select') {
      cancelConnect();
      setActiveTool('select');
    } else if (tool.id === 'connect') {
      // CU9: Entrar en modo conexión — el usuario clicará en el nodo origen
      setActiveTool('connect');
    } else {
      // CU8: Insertar elemento del tipo elegido
      cancelConnect();
      addNode(tool.id as NodeType);
      setActiveTool('select');
    }
  };

  // Atajos de teclado
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

  const tools = TOOLS.filter(t => t.group === 'tools');
  const elements = TOOLS.filter(t => t.group === 'elements');

  return (
    <div className="toolbar">
      {/* Herramientas */}
      <div className="toolbar__section-label">Herramientas</div>
      <div className="toolbar__group">
        {tools.map(t => (
          <button
            key={t.id}
            id={`tool-${t.id}`}
            className={`toolbar__btn${activeTool === t.id || (t.id === 'connect' && connectingSource) ? ' toolbar__btn--active' : ''}`}
            title={t.label}
            onClick={() => handleTool(t)}
          >
            {t.icon}
          </button>
        ))}
      </div>

      <div className="toolbar__sep" />

      {/* CU8: Elementos */}
      <div className="toolbar__section-label">Elementos</div>
      <div className="toolbar__group">
        {elements.map(t => (
          <button
            key={t.id}
            id={`tool-${t.id}`}
            className="toolbar__btn"
            title={t.label}
            onClick={() => handleTool(t)}
          >
            {t.icon}
          </button>
        ))}
      </div>

      <div className="toolbar__sep" />

      {/* Estado actual */}
      <div className="toolbar__status">
        {connectingSource
          ? <span className="toolbar__status--connecting"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight: 4, verticalAlign: 'middle'}}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></svg> Clic en destino</span>
          : <span className="toolbar__status--idle">Modo: {activeTool}</span>
        }
      </div>

      <div className="toolbar__sep" />

      <div className="toolbar__hint"><span>Ctrl+S</span><span>Guardar</span></div>
      <div className="toolbar__hint"><span>Rueda</span><span>Pan</span></div>
      <div className="toolbar__hint"><span>Ctrl+Rueda</span><span>Zoom</span></div>
    </div>
  );
};
