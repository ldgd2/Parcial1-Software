import React, { useState, useRef } from 'react';
import { Key, Link2, Lock } from 'lucide-react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import type { ClassNode as ClassNodeType } from '@/features/gestion_modelado/shared/types/types';
import './ClassNode.css';

interface Props {
  node: ClassNodeType;
  onDragStart: (e: React.MouseEvent) => void;
  onNodeClick?: (e: React.MouseEvent) => void;   // CU9: clic en modo conexión
  isConnectingMode?: boolean;                      // CU9: el canvas está en modo conexión
  isConnectingSource?: boolean;                    // CU9: este nodo es el origen seleccionado
}

const VISIBILIDADES = ['+', '-', '#'] as const;

export const ClassNode: React.FC<Props> = ({ node, onDragStart, onNodeClick, isConnectingMode = false, isConnectingSource = false }) => {
  const {
    selectedIds, setSelectedIds, updateNode, deleteNode,
    addAtributo, updateAtributo, deleteAtributo,
    addMetodo, updateMetodo, deleteMetodo,
    correcciones
  } = useDiagram();

  const { lockedElements, lockElement, unlockElement, refreshLock } = useRealTimeSync() || { lockedElements: {} };

  const isSelected = selectedIds.includes(node.id);
  // Solo bloqueamos la interacción general si alguien bloqueó el nodo entero (lo cual ya no debería pasar, pero por si acaso).
  
  
  const hasOpenCorrections = (correcciones[node.id] || []).some(c => c.estado === 'abierta');
  
  const [editingTitle, setEditingTitle] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  const handleFocus = (subId: string) => {
    if (lockElement) lockElement(`${node.id}:${subId}`);
  };
  const handleBlur = (subId: string) => {
    if (unlockElement) unlockElement(`${node.id}:${subId}`);
  };
  const handleChangeLock = (subId: string) => {
    if (refreshLock) refreshLock(`${node.id}:${subId}`);
  };
  const isLocked = (subId: string) => {
    return lockedElements[`${node.id}:${subId}`] !== undefined;
  };
  const lockedBy = (subId: string) => {
    return lockedElements[`${node.id}:${subId}`];
  };

  const handleTitleDblClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isLocked('nombre')) return;
    setEditingTitle(true);
    setTimeout(() => titleRef.current?.select(), 0);
  };

  const handleTitleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    updateNode(node.id, { nombre: e.target.value || node.nombre });
    setEditingTitle(false);
    handleBlur('nombre');
  };

  // Etiqueta de estereotipo según tipo
  const stereotypeLabel: Record<string, string> = {
    class: node.estereotipo === 'table' ? '«table»' : '«clase»',
    interface: '«interface»',
    abstract: '«abstracta»',
    enum: '«enum»',
    datatype: '«dataType»',
    primitive: '«primitive»',
    signal: '«signal»',
    note: '',
    part: '«part»',
    port: '«port»',
    expose_interface: '«expose_interface»',
    auxillary: '«auxillary»',
    focus: '«focus»',
    implementation_class: '«implementationClass»',
    realization_class: '«realization»',
    specification: '«specification»',
    type: '«type»',
    utility: '«utility»',
    artifact: '«artifact»',
    requirement: '«requirement»',
    issue: '«issue»',
    change: '«change»',
    information_item: '«informationItem»',
  };

  const getIconForType = (type: string) => {
    switch(type) {
      case 'interface': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" style={{marginRight:4}}><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/></svg>;
      case 'abstract': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/><path d="M9 16l3-8 3 8M10 13h4"/></svg>;
      case 'enum': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
      case 'part': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><line x1="4" y1="10" x2="20" y2="10"/></svg>;
      case 'port': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="8" y="8" width="8" height="8"/></svg>;
      case 'expose_interface': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><circle cx="12" cy="12" r="4"/><path d="M16 12h5M3 12h5"/></svg>;
      case 'artifact': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>;
      case 'requirement': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="3" y="5" width="18" height="14" rx="2" ry="2"/><path d="M9 10h6"/><path d="M9 14h6"/></svg>;
      case 'issue': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>;
      case 'change': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polygon points="12 2 22 8.5 22 21.5 12 15 2 21.5 2 8.5 12 2"/></svg>;
      case 'information_item': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>;
      case 'datatype': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>;
      case 'primitive': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="12" cy="12" r="3"/></svg>;
      case 'signal': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>;
      case 'auxillary':
      case 'focus':
      case 'implementation_class':
      case 'realization_class':
      case 'specification':
      case 'type':
      case 'utility':
        return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/><line x1="5" y1="8" x2="19" y2="8"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
      case 'class': 
      default:
        return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><rect x="3" y="4" width="18" height="16" rx="2" ry="2"/></svg>;
    }
  };

  // Si es nota, renderizar diferente
  if (node.type === 'note') {
    return (
      <div
        className={`class-node class-node--note${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: node.width }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        {isLocked('contenido') && (
          <div className="class-node__locked-overlay" style={{ position: 'absolute', top: -12, right: -12, background: 'var(--bg)', padding: '2px 6px', borderRadius: 12, border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 4, zIndex: 10, fontSize: 10, color: 'var(--text-secondary)' }}>
            <Lock size={10} /> {lockedBy('contenido')}
          </div>
        )}
        <div className="class-node__note-corner" />
        <textarea
          className="class-node__note-content"
          value={node.contenido || ''}
          onChange={e => { updateNode(node.id, { contenido: e.target.value }); handleChangeLock('contenido'); }}
          onFocus={() => handleFocus('contenido')}
          onBlur={() => handleBlur('contenido')}
          onMouseDown={e => e.stopPropagation()}
          onClick={e => e.stopPropagation()}
          rows={4}
          disabled={isLocked('contenido')}
        />
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} title="Eliminar nota"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  // Constraint
  if (node.type === 'constraint') {
    return (
      <div
        className={`class-node class-node--constraint${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: node.width, backgroundColor: '#fdf3f3', border: '1px solid #d99', borderRadius: 4, padding: '4px 8px', display: 'flex', position: 'absolute', cursor: 'grab' }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <span style={{color:'#a44', marginRight: 4}}>{'{'}</span>
        <textarea
          style={{ width: '100%', border: 'none', background: 'transparent', resize: 'none', outline: 'none', fontFamily: 'monospace' }}
          value={node.contenido || ''}
          onChange={e => { updateNode(node.id, { contenido: e.target.value }); handleChangeLock('contenido'); }}
          onFocus={() => handleFocus('contenido')}
          onBlur={() => handleBlur('contenido')}
          onMouseDown={e => e.stopPropagation()}
          onClick={e => e.stopPropagation()}
          rows={2}
          disabled={isLocked('contenido')}
        />
        <span style={{color:'#a44', marginLeft: 4}}>{'}'}</span>
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -10, right: -10 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  // Text Element
  if (node.type === 'text') {
    return (
      <div
        className={`class-node class-node--text${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: node.width, background: 'transparent', border: isSelected ? '1px dashed #999' : 'none', position: 'absolute', cursor: 'grab' }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <textarea
          style={{ width: '100%', border: 'none', background: 'transparent', resize: 'none', outline: 'none' }}
          value={node.contenido || ''}
          onChange={e => { updateNode(node.id, { contenido: e.target.value }); handleChangeLock('contenido'); }}
          onFocus={() => handleFocus('contenido')}
          onBlur={() => handleBlur('contenido')}
          onMouseDown={e => e.stopPropagation()}
          onClick={e => e.stopPropagation()}
          rows={2}
          placeholder="Texto libre..."
          disabled={isLocked('contenido')}
        />
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -10, right: -10 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  // Boundary
  if (node.type === 'boundary') {
    return (
      <div
        className={`class-node class-node--boundary${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: node.width || 200, height: 150, border: '2px dashed #666', background: 'rgba(0,0,0,0.02)', position: 'absolute', cursor: 'grab' }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <span style={{ position: 'absolute', top: -20, left: 0, fontWeight: 'bold' }}>{node.nombre || 'Boundary'}</span>
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -10, right: -10 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  // Renderizados Específicos para Composite Parts
  if (node.type === 'part') {
    return (
      <div
        className={`class-node class-node--part${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: node.width, minHeight: 60, borderColor: node.color, backgroundColor: '#cce5ff', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 4, position: 'absolute', cursor: 'grab', border: '1px solid #4a7fd4' }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <span style={{ fontWeight: 'bold', color: '#1a1f2e' }}>{node.nombre}</span>
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -10, right: -10 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  if (node.type === 'port') {
    return (
      <div
        className={`class-node class-node--port${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: 24, height: 24, backgroundColor: '#cce5ff', border: '1px solid #4a7fd4', position: 'absolute', cursor: 'grab', zIndex: 10 }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <span style={{ position: 'absolute', top: -20, left: 30, color: 'var(--text-primary)', fontSize: 12, whiteSpace: 'nowrap' }}>{node.nombre}</span>
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -15, right: -15 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  if (node.type === 'expose_interface') {
    return (
      <div
        className={`class-node class-node--expose${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: 30, height: 30, position: 'absolute', cursor: 'grab', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center' }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <div style={{ width: 20, height: 20, borderRadius: '50%', border: '2px solid #a8b5c8', backgroundColor: '#e2e8f0' }} />
        <span style={{ position: 'absolute', top: -20, color: 'var(--text-primary)', fontSize: 12, whiteSpace: 'nowrap' }}>{node.nombre}</span>
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -10, right: -20 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  // Eventos de UML Standard Profile
  if (node.type === 'create_event' || node.type === 'destroy_event') {
    return (
      <div
        className={`class-node class-node--event${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: 40, height: 40, position: 'absolute', cursor: 'grab', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
        onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
      >
        <svg width="40" height="40" viewBox="0 0 40 40" style={{ position: 'absolute' }}>
          <polygon points="20,2 38,20 20,38 2,20" fill="#6a1b9a" stroke="#4a148c" strokeWidth="2" />
        </svg>
        <span style={{ position: 'absolute', top: -22, color: 'var(--text-primary)', fontSize: 12, whiteSpace: 'nowrap', fontWeight: 'bold' }}>
          {node.type === 'create_event' ? 'Create' : 'Destroy'}
        </span>
        {isSelected && (
          <button className="class-node__delete" onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }} style={{ position: 'absolute', top: -10, right: -20 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>
    );
  }

  // Si es enum, renderizar valores
  const isEnum = node.type === 'enum';

  return (
    <div
      className={`class-node${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
      style={{ left: node.x, top: node.y, width: node.width, borderColor: node.color }}
      onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedIds([node.id]); } }}
      onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
    >
      {isSelected && <div className="class-node__select-bar" />}

      {/* Header */}
      <div
        className="class-node__header"
        style={{ background: node.color }}
        onDoubleClick={handleTitleDblClick}
      >
        <span className="class-node__stereotype">
          {getIconForType(node.type || 'class')}
          {stereotypeLabel[node.type ?? 'class']}
        </span>
        {isLocked('nombre') && !editingTitle && (
          <span style={{ fontSize: 10, marginLeft: 4 }}><Lock size={10}/> {lockedBy('nombre')}</span>
        )}
        {editingTitle ? (
          <input
            ref={titleRef}
            className="class-node__title-input"
            defaultValue={node.nombre}
            onBlur={handleTitleBlur}
            onChange={() => handleChangeLock('nombre')}
            onFocus={() => handleFocus('nombre')}
            onKeyDown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); }}
            onClick={e => e.stopPropagation()}
            onMouseDown={e => e.stopPropagation()}
            autoFocus
          />
        ) : (
          <div className="class-node__title">{node.nombre}</div>
        )}
        {isSelected && (
          <button
            className="class-node__delete"
            onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }}
            title="Eliminar"
          ><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        )}
      </div>

      {/* Attributes OR Enum values */}
      <div className="class-node__section">
        <div className="class-node__section-label">
          {isEnum ? 'VALORES' : 'ATRIBUTOS'}
          {isSelected && !isEnum && (
            <button className="class-node__add-btn" onClick={(e) => { e.stopPropagation(); addAtributo(node.id); }}>+</button>
          )}
        </div>
        {isEnum ? (
          // Enum values
          (node.valores || []).map((val, idx) => (
            <div key={idx} className="class-node__row">
              {isSelected ? (
                <>
                  <input
                    className="class-node__field-input"
                    value={val}
                    onChange={e => {
                      const newVals = [...(node.valores || [])];
                      newVals[idx] = e.target.value;
                      updateNode(node.id, { valores: newVals });
                      handleChangeLock(`val_${idx}`);
                    }}
                    onFocus={() => handleFocus(`val_${idx}`)}
                    onBlur={() => handleBlur(`val_${idx}`)}
                    disabled={isLocked(`val_${idx}`)}
                    onMouseDown={e => e.stopPropagation()}
                  />
                  {isLocked(`val_${idx}`) && <span title={lockedBy(`val_${idx}`)}><Lock size={10} /></span>}
                  <button
                    className="class-node__row-delete"
                    disabled={isLocked(`val_${idx}`)}
                    onClick={(e) => { e.stopPropagation(); const v = [...(node.valores || [])]; v.splice(idx, 1); updateNode(node.id, { valores: v }); }}
                  ><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                </>
              ) : (
                <span className="class-node__row-text">
                  {val} {isLocked(`val_${idx}`) && <Lock size={10} />}
                </span>
              )}
            </div>
          ))
        ) : (
          // Normal attributes / Table Columns
          node.atributos.map(attr => (
            <div key={attr.id} className="class-node__row">
              {isSelected ? (
              <>
                <select
                  className="class-node__vis-select"
                  value={attr.visibilidad}
                  onChange={e => { updateAtributo(node.id, attr.id, { visibilidad: e.target.value as any }); handleChangeLock(`attr_${attr.id}`); }}
                  onFocus={() => handleFocus(`attr_${attr.id}`)}
                  onBlur={() => handleBlur(`attr_${attr.id}`)}
                  disabled={isLocked(`attr_${attr.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                >
                  {node.estereotipo === 'table' ? (
                    <>
                      <option value="PK">PK</option>
                      <option value="FK">FK</option>
                      <option value="-">-</option>
                    </>
                  ) : (
                    VISIBILIDADES.map(v => <option key={v} value={v}>{v}</option>)
                  )}
                </select>
                <input
                  className="class-node__field-input"
                  value={attr.nombre}
                  onChange={e => { updateAtributo(node.id, attr.id, { nombre: e.target.value }); handleChangeLock(`attr_${attr.id}`); }}
                  onFocus={() => handleFocus(`attr_${attr.id}`)}
                  onBlur={() => handleBlur(`attr_${attr.id}`)}
                  disabled={isLocked(`attr_${attr.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                  placeholder={node.estereotipo === 'table' ? 'columna' : 'nombre'}
                />
                <span className="class-node__colon">:</span>
                <input
                  className="class-node__field-input class-node__field-input--type"
                  value={attr.tipo}
                  onChange={e => { updateAtributo(node.id, attr.id, { tipo: e.target.value }); handleChangeLock(`attr_${attr.id}`); }}
                  onFocus={() => handleFocus(`attr_${attr.id}`)}
                  onBlur={() => handleBlur(`attr_${attr.id}`)}
                  disabled={isLocked(`attr_${attr.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                  placeholder={node.estereotipo === 'table' ? 'INT, VARCHAR' : 'tipo'}
                />
                {isLocked(`attr_${attr.id}`) && <span title={lockedBy(`attr_${attr.id}`)}><Lock size={10} /></span>}
                <button
                  className="class-node__row-delete"
                  disabled={isLocked(`attr_${attr.id}`)}
                  onClick={(e) => { e.stopPropagation(); deleteAtributo(node.id, attr.id); }}
                ><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
              </>
            ) : (
              <span className="class-node__row-text">
                <span className="class-node__vis">
                  {attr.visibilidad === 'PK' ? (
                    <Key size={12} className="class-node__icon-pk" style={{ color: '#d4af37', marginRight: 4, verticalAlign: 'middle' }} />
                  ) : attr.visibilidad === 'FK' ? (
                    <Link2 size={12} className="class-node__icon-fk" style={{ color: '#3b82f6', marginRight: 4, verticalAlign: 'middle' }} />
                  ) : (
                    attr.visibilidad
                  )}
                </span>
                {attr.nombre}
                <span className="class-node__type"> {node.estereotipo === 'table' ? '' : ':'} {attr.tipo}</span>
                {isLocked(`attr_${attr.id}`) && <span title={lockedBy(`attr_${attr.id}`)}><Lock size={10} /></span>}
              </span>
            )}
          </div>
        ))
        )}
        {!isEnum && node.atributos.length === 0 && (
          <div className="class-node__empty">— sin atributos —</div>
        )}
        {isEnum && isSelected && (
          <button
            className="class-node__add-btn class-node__add-btn--block"
            onClick={(e) => { e.stopPropagation(); updateNode(node.id, { valores: [...(node.valores || []), 'NUEVO_VALOR'] }); }}
          >+ Valor</button>
        )}
      </div>

      {!isEnum && (
        <>
          <div className="class-node__divider" />

          {/* Methods / Restricciones section */}
          {node.estereotipo !== 'table' && (
          <div className="class-node__section">
        <div className="class-node__section-label">
          MÉTODOS
          {isSelected && (
            <button className="class-node__add-btn" onClick={(e) => { e.stopPropagation(); addMetodo(node.id); }}>+</button>
          )}
        </div>
        {node.metodos.map(met => (
          <div key={met.id} className="class-node__row">
            {isSelected ? (
              <>
                <select
                  className="class-node__vis-select"
                  value={met.visibilidad}
                  onChange={e => { updateMetodo(node.id, met.id, { visibilidad: e.target.value as any }); handleChangeLock(`met_${met.id}`); }}
                  onFocus={() => handleFocus(`met_${met.id}`)}
                  onBlur={() => handleBlur(`met_${met.id}`)}
                  disabled={isLocked(`met_${met.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                >
                  {VISIBILIDADES.map(v => <option key={v} value={v}>{v}</option>)}
                </select>
                <input
                  className="class-node__field-input"
                  value={met.nombre}
                  onChange={e => { updateMetodo(node.id, met.id, { nombre: e.target.value }); handleChangeLock(`met_${met.id}`); }}
                  onFocus={() => handleFocus(`met_${met.id}`)}
                  onBlur={() => handleBlur(`met_${met.id}`)}
                  disabled={isLocked(`met_${met.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                  placeholder="método"
                />
                <span className="class-node__colon">(</span>
                <input
                  className="class-node__field-input"
                  value={met.parametros}
                  onChange={e => { updateMetodo(node.id, met.id, { parametros: e.target.value }); handleChangeLock(`met_${met.id}`); }}
                  onFocus={() => handleFocus(`met_${met.id}`)}
                  onBlur={() => handleBlur(`met_${met.id}`)}
                  disabled={isLocked(`met_${met.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                  placeholder="params"
                />
                <span className="class-node__colon">):</span>
                <input
                  className="class-node__field-input class-node__field-input--type"
                  value={met.retorno}
                  onChange={e => { updateMetodo(node.id, met.id, { retorno: e.target.value }); handleChangeLock(`met_${met.id}`); }}
                  onFocus={() => handleFocus(`met_${met.id}`)}
                  onBlur={() => handleBlur(`met_${met.id}`)}
                  disabled={isLocked(`met_${met.id}`)}
                  onMouseDown={e => e.stopPropagation()}
                  placeholder="tipo"
                />
                {isLocked(`met_${met.id}`) && <span title={lockedBy(`met_${met.id}`)}><Lock size={10} /></span>}
                <button
                  className="class-node__row-delete"
                  disabled={isLocked(`met_${met.id}`)}
                  onClick={(e) => { e.stopPropagation(); deleteMetodo(node.id, met.id); }}
                ><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
              </>
            ) : (
              <span className="class-node__row-text">
                <span className="class-node__vis">{met.visibilidad}</span>
                {met.nombre}({met.parametros})
                <span className="class-node__type">: {met.retorno}</span>
                {isLocked(`met_${met.id}`) && <span title={lockedBy(`met_${met.id}`)}><Lock size={10} /></span>}
              </span>
            )}
          </div>
        ))}
        {node.metodos.length === 0 && (
          <div className="class-node__empty">— sin métodos —</div>
        )}
      </div>
      )}
      </>
      )}
    </div>
  );
};
