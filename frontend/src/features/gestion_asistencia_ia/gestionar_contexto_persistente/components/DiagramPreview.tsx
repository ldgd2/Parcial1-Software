import React, { useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { EstadoDiagramaVersion } from '../types';
import { firmaAtributo, firmaMetodo, type ComparacionVersiones, type EstadoCambio } from '../utils/versionDiff';
import './DiagramPreview.css';

interface Props {
  estado?: EstadoDiagramaVersion | null;
  /** Si se pasa, resalta lo agregado / eliminado / modificado */
  comparacion?: ComparacionVersiones | null;
  /** Qué lado de la comparación se está mostrando */
  lado?: 'antes' | 'despues';
  vacioTexto?: string;
}

// Medidas aproximadas de un ClassNode real, para ubicar cajas y relaciones
const ANCHO_POR_DEFECTO = 220;
const ALTO_CABECERA = 34;
const ALTO_FILA = 17;
const ALTO_SECCION = 12;
const MARGEN = 40;

function altoNodo(n: any): number {
  const atr = (n.atributos || []).length;
  const met = (n.metodos || []).length;
  return ALTO_CABECERA + ALTO_SECCION + Math.max(atr, 1) * ALTO_FILA + (met ? ALTO_SECCION + met * ALTO_FILA : 0) + 8;
}

/** Punto donde la línea entre los centros sale del borde de la caja. */
function bordeCaja(cx: number, cy: number, w: number, h: number, hacia: { x: number; y: number }) {
  const dx = hacia.x - cx;
  const dy = hacia.y - cy;
  if (dx === 0 && dy === 0) return { x: cx, y: cy };
  const escala = Math.min(Math.abs((w / 2) / (dx || 1e-9)), Math.abs((h / 2) / (dy || 1e-9)));
  return { x: cx + dx * escala, y: cy + dy * escala };
}

export const DiagramPreview: React.FC<Props> = ({ estado, comparacion, lado = 'antes', vacioTexto }) => {
  const contRef = useRef<HTMLDivElement>(null);
  const [tam, setTam] = useState({ w: 0, h: 0 });

  useLayoutEffect(() => {
    const el = contRef.current;
    if (!el) return;
    const medir = () => setTam({ w: el.clientWidth, h: el.clientHeight });
    medir();
    const ro = new ResizeObserver(medir);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const layout = useMemo(() => {
    const nodos = (estado?.nodes || []).map((n: any) => ({
      n,
      x: Number(n.x) || 0,
      y: Number(n.y) || 0,
      w: Number(n.width) || ANCHO_POR_DEFECTO,
      h: altoNodo(n),
    }));
    if (!nodos.length) return null;
    const minX = Math.min(...nodos.map(b => b.x)) - MARGEN;
    const minY = Math.min(...nodos.map(b => b.y)) - MARGEN;
    const maxX = Math.max(...nodos.map(b => b.x + b.w)) + MARGEN;
    const maxY = Math.max(...nodos.map(b => b.y + b.h)) + MARGEN;
    const porId = new Map(nodos.map(b => [String(b.n.id), b]));
    return { nodos, porId, minX, minY, ancho: maxX - minX, alto: maxY - minY };
  }, [estado]);

  const escala = layout && tam.w && tam.h ? Math.min(tam.w / layout.ancho, tam.h / layout.alto, 1.15) : 1;
  const offX = layout ? (tam.w - layout.ancho * escala) / 2 : 0;
  const offY = layout ? (tam.h - layout.alto * escala) / 2 : 0;

  const claseEstado = (e?: EstadoCambio) =>
    e && e !== 'igual' ? ` diagram-preview--${e}` : '';

  const estadoMiembro = (nodoId: string, firma: string): EstadoCambio | undefined => {
    const m = comparacion?.miembrosPorNodo[nodoId];
    if (!m) return undefined;
    if (lado === 'despues' && m.agregados.has(firma)) return 'agregado';
    if (lado === 'antes' && m.eliminados.has(firma)) return 'eliminado';
    if (m.modificados.has(firma)) return 'modificado';
    return undefined;
  };

  return (
    <div className="diagram-preview" ref={contRef} role="img" aria-label="Vista previa del diagrama (solo lectura)">
      {!layout ? (
        <div className="diagram-preview__vacio">{vacioTexto ?? 'La pizarra estaba vacía en esta versión.'}</div>
      ) : (
        <div
          className="diagram-preview__lienzo"
          style={{
            width: layout.ancho,
            height: layout.alto,
            transform: `translate(${offX}px, ${offY}px) scale(${escala})`,
          }}
        >
          <svg className="diagram-preview__relaciones" width={layout.ancho} height={layout.alto}>
            <defs>
              <marker id="dp-herencia" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="12" markerHeight="12" orient="auto">
                <path d="M1,1 L11,6 L1,11 Z" className="diagram-preview__punta-hueca" />
              </marker>
              <marker id="dp-flecha" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="10" markerHeight="10" orient="auto">
                <path d="M1,1 L11,6 L1,11" className="diagram-preview__punta-linea" />
              </marker>
              <marker id="dp-rombo-lleno" viewBox="0 0 16 10" refX="1" refY="5" markerWidth="16" markerHeight="10" orient="auto">
                <path d="M1,5 L8,1 L15,5 L8,9 Z" className="diagram-preview__punta-llena" />
              </marker>
              <marker id="dp-rombo-hueco" viewBox="0 0 16 10" refX="1" refY="5" markerWidth="16" markerHeight="10" orient="auto">
                <path d="M1,5 L8,1 L15,5 L8,9 Z" className="diagram-preview__punta-hueca" />
              </marker>
            </defs>
            {(estado?.relations || []).map((r: any) => {
              const a = layout.porId.get(String(r.sourceId));
              const b = layout.porId.get(String(r.targetId));
              if (!a || !b) return null;
              const ca = { x: a.x - layout.minX + a.w / 2, y: a.y - layout.minY + a.h / 2 };
              const cb = { x: b.x - layout.minX + b.w / 2, y: b.y - layout.minY + b.h / 2 };
              const p1 = bordeCaja(ca.x, ca.y, a.w, a.h, cb);
              const p2 = bordeCaja(cb.x, cb.y, b.w, b.h, ca);
              const tipo = r.type || 'association';
              const fin = tipo === 'inheritance' || tipo === 'realization' ? 'url(#dp-herencia)'
                : tipo === 'dependency' ? 'url(#dp-flecha)' : undefined;
              const inicio = tipo === 'composition' ? 'url(#dp-rombo-lleno)'
                : tipo === 'aggregation' ? 'url(#dp-rombo-hueco)' : undefined;
              const est = comparacion?.estadoRelacionPorId[String(r.id)];
              return (
                <line
                  key={r.id}
                  x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                  className={`diagram-preview__relacion${tipo === 'dependency' || tipo === 'realization' ? ' diagram-preview__relacion--punteada' : ''}${claseEstado(est)}`}
                  markerEnd={fin}
                  markerStart={inicio}
                />
              );
            })}
          </svg>

          {layout.nodos.map(({ n, x, y, w, h }) => {
            const id = String(n.id);
            const est = comparacion?.estadoPorId[id];
            return (
              <div
                key={id}
                className={`diagram-preview__nodo${claseEstado(est)}`}
                style={{ left: x - layout.minX, top: y - layout.minY, width: w, minHeight: h }}
              >
                <div className="diagram-preview__cabecera" style={{ background: n.color || 'var(--surface-color)' }}>
                  {n.type && n.type !== 'class' && <span className="diagram-preview__estereotipo">«{n.type}»</span>}
                  <span className="diagram-preview__titulo">{n.nombre}</span>
                </div>
                <div className="diagram-preview__seccion">
                  {(n.atributos || []).length === 0 && <div className="diagram-preview__fila diagram-preview__fila--vacia">sin atributos</div>}
                  {(n.atributos || []).map((a: any, i: number) => {
                    const firma = firmaAtributo(a);
                    return (
                      <div key={a.id ?? i} className={`diagram-preview__fila${claseEstado(estadoMiembro(id, firma))}`}>
                        {firma}
                      </div>
                    );
                  })}
                </div>
                {(n.metodos || []).length > 0 && (
                  <div className="diagram-preview__seccion">
                    {(n.metodos || []).map((m: any, i: number) => {
                      const firma = firmaMetodo(m);
                      return (
                        <div key={m.id ?? i} className={`diagram-preview__fila${claseEstado(estadoMiembro(id, firma))}`}>
                          {firma}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
