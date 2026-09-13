import React, { useState, useRef, useCallback, useEffect } from 'react';
import type { Relation, RelationType, RelationEndpoint, EndpointSide } from '@/features/gestion_modelado/shared/types/types';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import './RelationLayer.css';

interface NodePosition {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Pt { x: number; y: number }

interface Props {
  nodePositions: NodePosition[];
}

// ── Geometría ──────────────────────────────────────────────────────────────

/** Convierte RelationEndpoint a coordenadas absolutas, dado el nodo */
function endpointToPoint(node: NodePosition, ep: RelationEndpoint): Pt {
  const { x, y, width, height } = node;
  const t = Math.max(0, Math.min(1, ep.t));
  switch (ep.side) {
    case 'top':    return { x: x + width * t, y };
    case 'bottom': return { x: x + width * t, y: y + height };
    case 'left':   return { x,                y: y + height * t };
    case 'right':  return { x: x + width,     y: y + height * t };
  }
}

/** Punto en el borde del rect más cercano al punto externo */
function borderPoint(node: NodePosition, toX: number, toY: number): Pt {
  const cx = node.x + node.width / 2;
  const cy = node.y + node.height / 2;
  const dx = toX - cx;
  const dy = toY - cy;
  const hw = node.width / 2;
  const hh = node.height / 2;
  if (dx === 0 && dy === 0) return { x: cx, y: node.y };
  if (Math.abs(dx) * hh > Math.abs(dy) * hw) {
    const side = dx > 0 ? hw : -hw;
    return { x: cx + side, y: cy + (side / dx) * dy };
  } else {
    const side = dy > 0 ? hh : -hh;
    return { x: cx + (side / dy) * dx, y: cy + side };
  }
}

/** Dado un punto (px,py) cerca del borde de un nodo, calcula el RelationEndpoint más cercano */
function pointToEndpoint(node: NodePosition, px: number, py: number): RelationEndpoint {
  const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
  const dists: { side: EndpointSide; dist: number; t: number }[] = [
    { side: 'top',    dist: Math.abs(py - node.y),                t: clamp((px - node.x) / (node.width  || 1), 0, 1) },
    { side: 'bottom', dist: Math.abs(py - (node.y + node.height)), t: clamp((px - node.x) / (node.width  || 1), 0, 1) },
    { side: 'left',   dist: Math.abs(px - node.x),                t: clamp((py - node.y) / (node.height || 1), 0, 1) },
    { side: 'right',  dist: Math.abs(px - (node.x + node.width)), t: clamp((py - node.y) / (node.height || 1), 0, 1) },
  ];
  dists.sort((a, b) => a.dist - b.dist);
  return { side: dists[0].side, t: dists[0].t };
}

/** Clampea un punto al borde de un nodo (para preview en vivo) */
function clampToBorder(node: NodePosition, px: number, py: number): Pt {
  return endpointToPoint(node, pointToEndpoint(node, px, py));
}

function mouseToSvg(me: MouseEvent | React.MouseEvent, svg: SVGSVGElement): Pt {
  const rect = svg.getBoundingClientRect();
  const scaleX = (svg.viewBox?.baseVal?.width  || 8000) / rect.width;
  const scaleY = (svg.viewBox?.baseVal?.height || 8000) / rect.height;
  return {
    x: (me.clientX - rect.left) * scaleX - 2000,
    y: (me.clientY - rect.top)  * scaleY - 2000,
  };
}

// ── Marcadores ─────────────────────────────────────────────────────────────

function Markers() {
  return (
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#a8b5c8" />
      </marker>
      <marker id="triangle-empty" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0, 10 4, 0 8" fill="#1a1f2e" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
      <marker id="diamond-filled" markerWidth="14" markerHeight="8" refX="13" refY="4" orient="auto">
        <polygon points="0 4, 6 0, 12 4, 6 8" fill="#a8b5c8" />
      </marker>
      <marker id="diamond-empty" markerWidth="14" markerHeight="8" refX="13" refY="4" orient="auto">
        <polygon points="0 4, 6 0, 12 4, 6 8" fill="#1a1f2e" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
      <marker id="arrow-open" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polyline points="0 0, 9 4, 0 8" fill="none" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
      <marker id="socket" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">
        <path d="M10,0 C2,0 2,10 10,10" fill="none" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
      <marker id="ball" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <circle cx="5" cy="5" r="4" fill="none" stroke="#a8b5c8" strokeWidth="1.5" />
      </marker>
    </defs>
  );
}

function getLineStyle(type: RelationType, isVirtual: boolean): { stroke: string; strokeDasharray?: string; markerEnd: string; markerStart?: string } {
  if (isVirtual) return { stroke: '#a8b5c8', strokeDasharray: '6 4', markerEnd: '' };
  switch (type) {
    case 'inheritance':   return { stroke: '#a8b5c8', markerEnd: 'url(#triangle-empty)' };
    case 'realization':   return { stroke: '#a8b5c8', strokeDasharray: '6 4', markerEnd: 'url(#triangle-empty)' };
    case 'composition':   return { stroke: '#a8b5c8', markerEnd: 'url(#diamond-filled)' };
    case 'aggregation':   return { stroke: '#a8b5c8', markerEnd: 'url(#diamond-empty)' };
    case 'dependency':    return { stroke: '#a8b5c8', strokeDasharray: '6 4', markerEnd: 'url(#arrow)' };
    case 'directed':      return { stroke: '#a8b5c8', markerEnd: 'url(#arrow)' };
    case 'delegate':      return { stroke: '#a8b5c8', markerEnd: 'url(#arrow-open)' };
    case 'calls': case 'usage': case 'instantiate': case 'substitution':
    case 'abstraction': case 'create': case 'send': case 'trace':
      return { stroke: '#a8b5c8', strokeDasharray: '6 4', markerEnd: 'url(#arrow-open)' };
    case 'assembly':      return { stroke: '#a8b5c8', markerEnd: 'url(#socket)', markerStart: 'url(#ball)' };
    case 'connector':     return { stroke: '#a8b5c8', markerEnd: '' };
    case '1:1': case '1:N': case 'N:M':
    case '0..1:1': case '0..1:N': case '0..N:1': case '0..N:M':
      return { stroke: '#e8bc56', markerEnd: type.includes('N') || type.includes('M') ? 'url(#arrow)' : '' };
    case 'association':   return { stroke: '#fbd38d', markerEnd: '' };
    default:              return { stroke: '#a8b5c8', markerEnd: '' };
  }
}

// ── Crosshair guide ────────────────────────────────────────────────────────

interface CrosshairProps { x: number; y: number }
const Crosshair: React.FC<CrosshairProps> = ({ x, y }) => (
  <g style={{ pointerEvents: 'none' }}>
    <line x1={-2000} y1={y} x2={6000} y2={y}
      stroke="rgba(100,255,218,0.25)" strokeWidth={1} strokeDasharray="4 4" />
    <line x1={x} y1={-2000} x2={x} y2={6000}
      stroke="rgba(100,255,218,0.25)" strokeWidth={1} strokeDasharray="4 4" />
  </g>
);

// ── WaypointHandle ─────────────────────────────────────────────────────────

interface WaypointHandleProps {
  pt: Pt;
  index: number;
  svgEl: SVGSVGElement | null;
  onMove: (index: number, pt: Pt) => void;
  onDoubleClick: (index: number) => void;
  onDragLive: (pt: Pt | null) => void;
}

const WaypointHandle: React.FC<WaypointHandleProps> = ({ pt, index, svgEl, onMove, onDoubleClick, onDragLive }) => {
  const [live, setLive] = useState<Pt>(pt);
  const dragging = useRef(false);
  useEffect(() => { setLive(pt); }, [pt]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!svgEl) return;
    dragging.current = true;

    const onMove_ = (me: MouseEvent) => {
      if (!dragging.current) return;
      const p = mouseToSvg(me, svgEl);
      setLive(p);
      onDragLive(p);
    };
    const onUp = (me: MouseEvent) => {
      dragging.current = false;
      window.removeEventListener('mousemove', onMove_);
      window.removeEventListener('mouseup', onUp);
      onDragLive(null);
      onMove(index, mouseToSvg(me, svgEl));
    };
    window.addEventListener('mousemove', onMove_);
    window.addEventListener('mouseup', onUp);
  };

  return (
    <circle cx={live.x} cy={live.y} r={5}
      fill="#64ffda" stroke="#1a1f2e" strokeWidth={1.5}
      style={{ cursor: 'move' }}
      onMouseDown={onMouseDown}
      onDoubleClick={(e) => { e.stopPropagation(); onDoubleClick(index); }}
    />
  );
};

// ── EndpointHandle: arrastrable, snaps al borde del nodo ──────────────────

interface EndpointHandleProps {
  pt: Pt;
  node: NodePosition;
  svgEl: SVGSVGElement | null;
  onDragEnd: (ep: RelationEndpoint) => void;
  onDragLive: (pt: Pt | null) => void;
}

const EndpointHandle: React.FC<EndpointHandleProps> = ({ pt, node, svgEl, onDragEnd, onDragLive }) => {
  const [live, setLive] = useState<Pt>(pt);
  const dragging = useRef(false);
  useEffect(() => { setLive(pt); }, [pt]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!svgEl) return;
    dragging.current = true;

    const onMove_ = (me: MouseEvent) => {
      if (!dragging.current) return;
      const { x, y } = mouseToSvg(me, svgEl);
      const snapped = clampToBorder(node, x, y);
      setLive(snapped);
      onDragLive(snapped);
    };
    const onUp = (me: MouseEvent) => {
      dragging.current = false;
      window.removeEventListener('mousemove', onMove_);
      window.removeEventListener('mouseup', onUp);
      onDragLive(null);
      const { x, y } = mouseToSvg(me, svgEl);
      onDragEnd(pointToEndpoint(node, x, y));
    };
    window.addEventListener('mousemove', onMove_);
    window.addEventListener('mouseup', onUp);
  };

  return (
    <circle cx={live.x} cy={live.y} r={6}
      fill="#f6ad55" stroke="#1a1f2e" strokeWidth={1.5}
      style={{ cursor: 'ew-resize' }}
      onMouseDown={onMouseDown}
    />
  );
};

// ── RelationLine ───────────────────────────────────────────────────────────

interface RelationLineProps {
  relation: Relation;
  positions: Map<string, NodePosition>;
  onDelete: (id: string) => void;
  onUpdateLabel: (id: string, label: string) => void;
  svgEl: SVGSVGElement | null;
}

const STEREOTYPE_TYPES = new Set(['delegate', 'calls', 'usage', 'instantiate', 'substitution', 'abstraction', 'trace', 'create', 'send', 'connector']);

const RelationLine: React.FC<RelationLineProps> = ({ relation, positions, onDelete, onUpdateLabel, svgEl }) => {
  const [hovered, setHovered] = useState(false);
  const [editingLabel, setEditingLabel] = useState(false);
  const [labelValue, setLabelValue] = useState(relation.label || '');
  const [editingSource, setEditingSource] = useState(false);
  const [sourceValue, setSourceValue] = useState(relation.sourceLabel || '');
  const [editingTarget, setEditingTarget] = useState(false);
  const [targetValue, setTargetValue] = useState(relation.targetLabel || '');
  const [crosshair, setCrosshair] = useState<Pt | null>(null);

  const { updateRelation, setSelectedIds, selectedIds, correcciones } = useDiagram();

  const src = positions.get(relation.sourceId);
  const tgt = positions.get(relation.targetId);
  if (!src || !tgt) return null;

  const isSelected = selectedIds.includes(relation.id);
  const hasOpenCorrections = (correcciones[relation.id] || []).some(c => c.estado === 'abierta');

  const wps: Pt[] = relation.waypoints ?? [];
  const isVirtual = src.width === 0 || tgt.width === 0;
  const style = getLineStyle(relation.type, isVirtual);
  const stroke = hasOpenCorrections ? '#ef4444' : (isSelected ? '#64ffda' : style.stroke);
  const sw = hovered || isSelected ? 2.5 : (hasOpenCorrections ? 2 : 1.5);

  // ── Calcular puntos de la polilínea ────────────────────────────────────
  let srcPt: Pt, tgtPt: Pt;
  let points: Pt[];

  if (relation.sourceId === relation.targetId) {
    // Auto-referencia
    const offset = 40;
    srcPt = relation.sourceEndpoint
      ? endpointToPoint(src, relation.sourceEndpoint)
      : { x: src.x + src.width, y: src.y + src.height * 0.3 };
    tgtPt = relation.targetEndpoint
      ? endpointToPoint(src, relation.targetEndpoint)
      : { x: src.x + src.width * 0.7, y: src.y };
    if (wps.length === 0) {
      points = [
        srcPt,
        { x: src.x + src.width + offset, y: srcPt.y },
        { x: src.x + src.width + offset, y: src.y - offset },
        { x: tgtPt.x, y: src.y - offset },
        tgtPt,
      ];
    } else {
      points = [srcPt, ...wps, tgtPt];
    }
  } else {
    // Relación normal
    if (relation.sourceEndpoint) {
      srcPt = endpointToPoint(src, relation.sourceEndpoint);
    } else {
      const firstTarget = wps.length > 0 ? wps[0] : { x: tgt.x + tgt.width / 2, y: tgt.y + tgt.height / 2 };
      srcPt = borderPoint(src, firstTarget.x, firstTarget.y);
    }

    if (relation.targetEndpoint) {
      tgtPt = endpointToPoint(tgt, relation.targetEndpoint);
    } else {
      const lastSource = wps.length > 0 ? wps[wps.length - 1] : { x: src.x + src.width / 2, y: src.y + src.height / 2 };
      tgtPt = borderPoint(tgt, lastSource.x, lastSource.y);
    }

    points = [srcPt, ...wps, tgtPt];
  }

  const pointsStr = points.map(p => `${p.x},${p.y}`).join(' ');
  const midIdx = Math.floor(points.length / 2);
  const mA = points[midIdx - 1] ?? points[0];
  const mB = points[midIdx]   ?? points[points.length - 1];
  const midX = (mA.x + mB.x) / 2;
  const midY = (mA.y + mB.y) / 2;

  // ── Drag de segmento: añade waypoint ──────────────────────────────────
  const onSegmentMouseDown = useCallback((insertIdx: number, e: React.MouseEvent) => {
    if (!svgEl) return;
    e.stopPropagation();
    e.preventDefault();
    let moved = false;

    const onMove_ = (_me: MouseEvent) => { moved = true; };
    const onUp = (me: MouseEvent) => {
      window.removeEventListener('mousemove', onMove_);
      window.removeEventListener('mouseup', onUp);
      if (!moved) return;
      const p = mouseToSvg(me, svgEl);
      const newWps = [...wps];
      newWps.splice(insertIdx, 0, p);
      updateRelation(relation.id, { waypoints: newWps });
    };
    window.addEventListener('mousemove', onMove_);
    window.addEventListener('mouseup', onUp);
  }, [svgEl, wps, relation.id, updateRelation]);

  const moveWaypoint = useCallback((idx: number, pt: Pt) => {
    const newWps = [...wps];
    newWps[idx] = pt;
    updateRelation(relation.id, { waypoints: newWps });
  }, [wps, relation.id, updateRelation]);

  const deleteWaypoint = useCallback((idx: number) => {
    const newWps = [...wps];
    newWps.splice(idx, 1);
    updateRelation(relation.id, { waypoints: newWps });
  }, [wps, relation.id, updateRelation]);

  const isSelfLoop = relation.sourceId === relation.targetId;

  return (
    <g onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>

      {/* Crosshair durante drag de waypoint */}
      {crosshair && <Crosshair x={crosshair.x} y={crosshair.y} />}

      {/* Hit areas de segmentos (para insertar waypoints) */}
      {points.slice(0, -1).map((p, i) => (
        <line key={`seg-hit-${i}`}
          x1={p.x} y1={p.y} x2={points[i+1].x} y2={points[i+1].y}
          stroke="transparent" strokeWidth={14}
          style={{ cursor: 'crosshair' }}
          onMouseDown={(e) => { e.stopPropagation(); setSelectedIds([relation.id]); onSegmentMouseDown(i, e); }}
          onClick={(e) => { e.stopPropagation(); setSelectedIds([relation.id]); }}
        />
      ))}

      {/* Polilínea visual */}
      <polyline
        points={pointsStr}
        stroke={stroke} strokeWidth={sw}
        strokeDasharray={style.strokeDasharray}
        markerEnd={style.markerEnd} markerStart={style.markerStart}
        fill="none" style={{ pointerEvents: 'none' }}
      />

      {/* Etiqueta estereotipo */}
      {STEREOTYPE_TYPES.has(relation.type) && (
        <text x={midX} y={midY - 8} fill="#a8b5c8" fontSize="12" textAnchor="middle" style={{ pointerEvents: 'none' }}>
          {`«${relation.type}»`}
        </text>
      )}

      {/* Multiplicidad origen */}
      {!isVirtual && (editingSource ? (
        <foreignObject x={srcPt.x + 4} y={srcPt.y - 20} width={60} height={22}>
          <input autoFocus value={sourceValue} onChange={e => setSourceValue(e.target.value)}
            onBlur={() => { setEditingSource(false); updateRelation(relation.id, { sourceLabel: sourceValue }); }}
            onKeyDown={e => { if (e.key === 'Enter') { setEditingSource(false); updateRelation(relation.id, { sourceLabel: sourceValue }); }}}
            style={{ width: '100%', background: '#1a1f2e', color: '#fff', border: '1px solid #a8b5c8', borderRadius: 4, padding: '1px 4px', fontSize: 10 }} />
        </foreignObject>
      ) : (
        <text x={srcPt.x + 8} y={srcPt.y - 5} fill="#a8b5c8" fontSize="11"
          onClick={e => { e.stopPropagation(); setEditingSource(true); }} style={{ cursor: 'text' }}>
          {relation.sourceLabel}
        </text>
      ))}

      {/* Multiplicidad destino */}
      {!isVirtual && (editingTarget ? (
        <foreignObject x={tgtPt.x - 64} y={tgtPt.y - 20} width={60} height={22}>
          <input autoFocus value={targetValue} onChange={e => setTargetValue(e.target.value)}
            onBlur={() => { setEditingTarget(false); updateRelation(relation.id, { targetLabel: targetValue }); }}
            onKeyDown={e => { if (e.key === 'Enter') { setEditingTarget(false); updateRelation(relation.id, { targetLabel: targetValue }); }}}
            style={{ width: '100%', background: '#1a1f2e', color: '#fff', border: '1px solid #a8b5c8', borderRadius: 4, padding: '1px 4px', fontSize: 10 }} />
        </foreignObject>
      ) : (
        <text x={tgtPt.x - 8} y={tgtPt.y - 5} fill="#a8b5c8" fontSize="11" textAnchor="end"
          onDoubleClick={() => setEditingTarget(true)} style={{ cursor: 'text' }}>
          {relation.targetLabel || (hovered ? '...' : '')}
        </text>
      ))}

      {/* Etiqueta central */}
      {!STEREOTYPE_TYPES.has(relation.type) && (editingLabel ? (
        <foreignObject x={midX - 60} y={midY - 12} width={120} height={24}>
          <input autoFocus value={labelValue} onChange={e => setLabelValue(e.target.value)}
            onBlur={() => { setEditingLabel(false); onUpdateLabel(relation.id, labelValue); }}
            onKeyDown={e => { if (e.key === 'Enter') { setEditingLabel(false); onUpdateLabel(relation.id, labelValue); }}}
            style={{ width: '100%', background: '#1a1f2e', color: '#fff', border: '1px solid #a8b5c8', borderRadius: 4, padding: '2px 6px', fontSize: 11 }} />
        </foreignObject>
      ) : (
        <text x={midX} y={midY - 6} className="relation-layer__label" textAnchor="middle"
          onDoubleClick={() => setEditingLabel(true)}>
          {relation.label || (hovered ? '✎' : '')}
        </text>
      ))}

      {/* ── Handles (solo cuando seleccionado) ── */}
      {isSelected && (
        <>
          {/* Endpoint origen (naranja) */}
          <EndpointHandle
            pt={srcPt}
            node={src}
            svgEl={svgEl}
            onDragEnd={ep => updateRelation(relation.id, { sourceEndpoint: ep })}
            onDragLive={p => setCrosshair(p)}
          />
          {/* Endpoint destino (naranja) — para self-loop usa src */}
          <EndpointHandle
            pt={tgtPt}
            node={isSelfLoop ? src : tgt}
            svgEl={svgEl}
            onDragEnd={ep => updateRelation(relation.id, { targetEndpoint: ep })}
            onDragLive={p => setCrosshair(p)}
          />
          {/* Waypoints intermedios (turquesa) */}
          {wps.map((wp, i) => (
            <WaypointHandle key={`wp-${i}`}
              pt={wp} index={i} svgEl={svgEl}
              onMove={moveWaypoint}
              onDoubleClick={deleteWaypoint}
              onDragLive={p => setCrosshair(p)}
            />
          ))}
        </>
      )}

      {/* Botón eliminar */}
      {hovered && (
        <g>
          <circle cx={midX} cy={midY + 14} r={9} fill="#c0392b" opacity={0.9}
            style={{ cursor: 'pointer' }} onClick={() => onDelete(relation.id)} />
          <text x={midX} y={midY + 18} textAnchor="middle" fontSize={11} fill="#fff"
            style={{ cursor: 'pointer', pointerEvents: 'none' }}>×</text>
        </g>
      )}
    </g>
  );
};

// ── RelationLayer ──────────────────────────────────────────────────────────

export const RelationLayer: React.FC<Props> = ({ nodePositions }) => {
  const { relations, deleteRelation, updateRelation } = useDiagram();
  const svgRef = useRef<SVGSVGElement>(null);

  const posMap = new Map<string, NodePosition>(nodePositions.map(p => [p.id, p]));

  // Registrar relaciones como nodos virtuales para AssociationClass
  relations.forEach(rel => {
    const src = posMap.get(rel.sourceId);
    const tgt = posMap.get(rel.targetId);
    if (src && tgt && rel.sourceId !== rel.targetId && src.width > 0 && tgt.width > 0) {
      const wps = rel.waypoints ?? [];
      const firstTarget = wps.length > 0 ? wps[0] : { x: tgt.x + tgt.width / 2, y: tgt.y + tgt.height / 2 };
      const lastSource  = wps.length > 0 ? wps[wps.length - 1] : { x: src.x + src.width / 2, y: src.y + src.height / 2 };
      const p1 = borderPoint(src, firstTarget.x, firstTarget.y);
      const p2 = borderPoint(tgt, lastSource.x, lastSource.y);
      posMap.set(rel.id, { id: rel.id, x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2, width: 0, height: 0 });
    }
  });

  return (
    <svg
      ref={svgRef}
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
              svgEl={svgRef.current}
            />
          ))}
        </g>
      </g>
    </svg>
  );
};
