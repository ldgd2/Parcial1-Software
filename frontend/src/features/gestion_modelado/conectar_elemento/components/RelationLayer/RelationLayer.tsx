import React, { useState } from 'react';
import type { Relation, RelationType } from '@/features/gestion_modelado/shared/types/types';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import './RelationLayer.css';

interface NodePosition {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Props {
  nodePositions: NodePosition[];
}

// Calcula el punto de borde más cercano al centro del otro nodo
function getBorderPoint(node: NodePosition, targetX: number, targetY: number) {
  const cx = node.x + node.width / 2;
  const cy = node.y + node.height / 2;
  const dx = targetX - cx;
  const dy = targetY - cy;
  const angle = Math.atan2(dy, dx);
  const hw = node.width / 2;
  const hh = node.height / 2;
  // Intersección con el borde del rectángulo
  if (Math.abs(Math.cos(angle)) * hh > Math.abs(Math.sin(angle)) * hw) {
    const x = cx + (Math.cos(angle) > 0 ? hw : -hw);
    const y = cy + Math.tan(angle) * (Math.cos(angle) > 0 ? hw : -hw);
    return { x, y };
  } else {
    const y = cy + (Math.sin(angle) > 0 ? hh : -hh);
    const x = cx + (1 / Math.tan(angle)) * (Math.sin(angle) > 0 ? hh : -hh);
    return { x, y };
  }
}

// Marcadores SVG según tipo de relación
function Markers() {
  return (
    <defs>
      {/* Flecha simple → Asociación / Dirigida */}
      <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#a8b5c8" />
      </marker>
      {/* Triángulo vacío → Herencia / Realización */}
      <marker id="triangle-empty" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0, 10 4, 0 8" fill="#1a1f2e" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
      {/* Rombo relleno → Composición */}
      <marker id="diamond-filled" markerWidth="12" markerHeight="8" refX="11" refY="4" orient="auto">
        <polygon points="0 4, 6 0, 12 4, 6 8" fill="#a8b5c8" />
      </marker>
      {/* Rombo vacío → Agregación */}
      <marker id="diamond-empty" markerWidth="12" markerHeight="8" refX="11" refY="4" orient="auto">
        <polygon points="0 4, 6 0, 12 4, 6 8" fill="#1a1f2e" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
    </defs>
  );
}

function getLineStyle(type: RelationType): { stroke: string; strokeDasharray?: string; markerEnd: string } {
  switch (type) {
    case 'inheritance':   return { stroke: '#a8b5c8', markerEnd: 'url(#triangle-empty)' };
    case 'realization':   return { stroke: '#a8b5c8', strokeDasharray: '6 4', markerEnd: 'url(#triangle-empty)' };
    case 'composition':   return { stroke: '#a8b5c8', markerEnd: 'url(#diamond-filled)' };
    case 'aggregation':   return { stroke: '#a8b5c8', markerEnd: 'url(#diamond-empty)' };
    case 'dependency':    return { stroke: '#a8b5c8', strokeDasharray: '6 4', markerEnd: 'url(#arrow)' };
    case 'directed':      return { stroke: '#a8b5c8', markerEnd: 'url(#arrow)' };
    case '1:1':           
    case '1:N':           
    case 'N:M':           
    case '0..1:1':        
    case '0..1:N':        
    case '0..N:1':        
    case '0..N:M':        return { stroke: '#e8bc56', markerEnd: type.includes('N') || type.includes('M') ? (type === '0..N:1' || type === '1:1' ? '' : 'url(#arrow)') : '' };
    case 'association':
    default:              return { stroke: '#a8b5c8', markerEnd: '' };
  }
}

interface RelationLineProps {
  relation: Relation;
  positions: Map<string, NodePosition>;
  onDelete: (id: string) => void;
  onUpdateLabel: (id: string, label: string) => void;
}

const RelationLine: React.FC<RelationLineProps> = ({ relation, positions, onDelete, onUpdateLabel }) => {
  const [hovered, setHovered] = useState(false);
  const [editingLabel, setEditingLabel] = useState(false);
  const [labelValue, setLabelValue] = useState(relation.label || '');
  
  const [editingSource, setEditingSource] = useState(false);
  const [sourceValue, setSourceValue] = useState(relation.sourceLabel || '');
  
  const [editingTarget, setEditingTarget] = useState(false);
  const [targetValue, setTargetValue] = useState(relation.targetLabel || '');

  const src = positions.get(relation.sourceId);
  const tgt = positions.get(relation.targetId);
  if (!src || !tgt) return null;

  const srcCenter = { x: src.x + src.width / 2, y: src.y + src.height / 2 };
  const tgtCenter = { x: tgt.x + tgt.width / 2, y: tgt.y + tgt.height / 2 };
  const p1 = getBorderPoint(src, tgtCenter.x, tgtCenter.y);
  const p2 = getBorderPoint(tgt, srcCenter.x, srcCenter.y);

  const midX = (p1.x + p2.x) / 2;
  const midY = (p1.y + p2.y) / 2;

  const style = getLineStyle(relation.type);
  
  const { updateRelation, setSelectedId, selectedId, correcciones } = useDiagram();
  
  const hasOpenCorrections = (correcciones[relation.id] || []).some(c => c.estado === 'abierta');
  const baseStroke = hasOpenCorrections ? '#ef4444' : style.stroke;
  const highlightStroke = selectedId === relation.id ? '#64ffda' : baseStroke;

  return (
    <g
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <line
        x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
        stroke="transparent"
        strokeWidth={12}
        style={{ cursor: 'pointer' }}
        onClick={(e) => {
          e.stopPropagation();
          setHovered(h => !h);
          setSelectedId(relation.id);
        }}
      />
      <line
        x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
        stroke={highlightStroke}
        strokeWidth={hovered || selectedId === relation.id ? 2.5 : (hasOpenCorrections ? 2 : 1.5)}
        strokeDasharray={style.strokeDasharray}
        markerEnd={style.markerEnd}
        style={{ pointerEvents: 'none' }}
      />

      {/* Source Label (Cardinality) */}
      {editingSource ? (
        <foreignObject x={p1.x} y={p1.y - 12} width={60} height={24}>
          <input
            autoFocus
            value={sourceValue}
            onChange={e => setSourceValue(e.target.value)}
            onBlur={() => { setEditingSource(false); updateRelation(relation.id, { sourceLabel: sourceValue }); }}
            onKeyDown={e => { if (e.key === 'Enter') { setEditingSource(false); updateRelation(relation.id, { sourceLabel: sourceValue }); } }}
            style={{ width: '100%', background: '#1a1f2e', color: '#fff', border: '1px solid #a8b5c8', borderRadius: 4, padding: '2px 4px', fontSize: 10 }}
          />
        </foreignObject>
      ) : (
        <text 
          x={p1.x + 12} y={p1.y - 5} 
          className="relation-layer__label-small"
          onDoubleClick={() => setEditingSource(true)}
          style={{ cursor: 'text' }}
        >
          {relation.sourceLabel || (hovered ? '...' : '')}
        </text>
      )}

      {/* Target Label (Cardinality) */}
      {editingTarget ? (
        <foreignObject x={p2.x - 60} y={p2.y - 12} width={60} height={24}>
          <input
            autoFocus
            value={targetValue}
            onChange={e => setTargetValue(e.target.value)}
            onBlur={() => { setEditingTarget(false); updateRelation(relation.id, { targetLabel: targetValue }); }}
            onKeyDown={e => { if (e.key === 'Enter') { setEditingTarget(false); updateRelation(relation.id, { targetLabel: targetValue }); } }}
            style={{ width: '100%', background: '#1a1f2e', color: '#fff', border: '1px solid #a8b5c8', borderRadius: 4, padding: '2px 4px', fontSize: 10 }}
          />
        </foreignObject>
      ) : (
        <text 
          x={p2.x - 12} y={p2.y - 5} 
          className="relation-layer__label-small" 
          textAnchor="end"
          onDoubleClick={() => setEditingTarget(true)}
          style={{ cursor: 'text' }}
        >
          {relation.targetLabel || (hovered ? '...' : '')}
        </text>
      )}

      {/* Etiqueta central editable */}
      {editingLabel ? (
        <foreignObject x={midX - 60} y={midY - 12} width={120} height={24}>
          <input
            autoFocus
            value={labelValue}
            onChange={e => setLabelValue(e.target.value)}
            onBlur={() => { setEditingLabel(false); onUpdateLabel(relation.id, labelValue); }}
            onKeyDown={e => { if (e.key === 'Enter') { setEditingLabel(false); onUpdateLabel(relation.id, labelValue); } }}
            style={{ width: '100%', background: '#1a1f2e', color: '#fff', border: '1px solid #a8b5c8', borderRadius: 4, padding: '2px 6px', fontSize: 11 }}
          />
        </foreignObject>
      ) : (
        <text
          x={midX} y={midY - 6}
          className="relation-layer__label"
          textAnchor="middle"
          onDoubleClick={() => setEditingLabel(true)}
        >
          {relation.label || (hovered ? '✎' : '')}
        </text>
      )}

      {/* Botón de eliminar al hacer hover */}
      {hovered && (
        <g>
          <circle cx={midX} cy={midY + 14} r={9} fill="#c0392b" opacity={0.9} style={{ cursor: 'pointer' }} onClick={() => onDelete(relation.id)} />
          <text x={midX} y={midY + 18} textAnchor="middle" fontSize={11} fill="#fff" style={{ cursor: 'pointer', pointerEvents: 'none' }}>×</text>
        </g>
      )}
    </g>
  );
};

// ─── RelationLayer: superpuesto sobre el canvas SVG ─────────────────────────

export const RelationLayer: React.FC<Props> = ({ nodePositions }) => {
  const { relations, deleteRelation, updateRelation } = useDiagram();

  const posMap = new Map<string, NodePosition>(nodePositions.map(p => [p.id, p]));

  return (
    <svg
      className="relation-layer"
      style={{ position: 'absolute', top: -2000, left: -2000, width: 8000, height: 8000, pointerEvents: 'none', overflow: 'visible' }}
    >
      <g transform="translate(2000, 2000)">
        <Markers />
        <g style={{ pointerEvents: 'all' }}>
          {relations.map(rel => (
            <RelationLine
              key={rel.id}
              relation={rel}
              positions={posMap}
              onDelete={id => deleteRelation(id)}
              onUpdateLabel={(id, label) => updateRelation(id, { label })}
            />
          ))}
        </g>
      </g>
    </svg>
  );
};
