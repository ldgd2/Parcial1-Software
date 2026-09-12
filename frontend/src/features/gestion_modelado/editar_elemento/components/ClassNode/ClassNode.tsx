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
    selectedId, setSelectedId, updateNode, deleteNode,
    addAtributo, updateAtributo, deleteAtributo,
    addMetodo, updateMetodo, deleteMetodo,
    correcciones
  } = useDiagram();

  const { lockedElements, lockElement, unlockElement, refreshLock } = useRealTimeSync() || { lockedElements: {} };

  const isSelected = selectedId === node.id;
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
    note: '',
  };

  // Si es nota, renderizar diferente
  if (node.type === 'note') {
    return (
      <div
        className={`class-node class-node--note${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
        style={{ left: node.x, top: node.y, width: node.width }}
        onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedId(node.id); } }}
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

  // Si es enum, renderizar valores
  const isEnum = node.type === 'enum';

  return (
    <div
      className={`class-node${isSelected ? ' class-node--selected' : ''}${isConnectingMode ? ' class-node--connectable' : ''}${isConnectingSource ? ' class-node--connect-source' : ''}${hasOpenCorrections ? ' class-node--has-corrections' : ''}`}
      style={{ left: node.x, top: node.y, width: node.width, borderColor: node.color }}
      onClick={(e) => { e.stopPropagation(); if (onNodeClick) { onNodeClick(e); } else { setSelectedId(node.id); } }}
      onMouseDown={(e) => { e.stopPropagation(); onDragStart(e); }}
    >
      {isSelected && <div className="class-node__select-bar" />}

      {/* Header */}
      <div
        className="class-node__header"
        style={{ background: node.color }}
        onDoubleClick={handleTitleDblClick}
      >
        <span className="class-node__stereotype">{stereotypeLabel[node.type ?? 'class']}</span>
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
    </div>
  );
};
