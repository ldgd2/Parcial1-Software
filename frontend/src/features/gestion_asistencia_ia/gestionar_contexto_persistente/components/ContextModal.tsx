import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { ContextoIAResponse, EstadoDiagramaVersion, VersionDetalle, VersionResumen } from '../types';
import { useVersionesContexto } from '../hooks/useVersionesContexto';
import { compararVersiones } from '../utils/versionDiff';
import { DiagramPreview } from './DiagramPreview';
import { MemoriaPanel } from './MemoriaPanel';
import { ContribucionPanel } from './ContribucionPanel';
import { exportarPdf, exportarPng, exportarSvg } from '@/features/gestion_modelado/shared/utils/exportarDiagrama';
import './ContextModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  contexto: ContextoIAResponse | null;
  onReiniciar: () => Promise<any>;
  /** Necesario para el historial de versiones */
  proyectoId?: number;
  /** El usuario tiene permiso de edición en la sala */
  puedeRestaurar?: boolean;
  /** Aplica `estado` a la pizarra de toda la sala */
  onRestaurar?: (estado: EstadoDiagramaVersion, version: VersionResumen, lado: Lado) => Promise<void>;
  /** Abrir directamente en esta versión (p. ej. desde una propuesta del chat) */
  versionInicial?: number | null;
  /** Correcciones del diagrama en vivo (Panel de propiedades de cada clase) */
  correccionesDiagrama?: Array<{ id: string; target: string; text: string; estado: string }>;
}

type Pestana = 'historial' | 'proyecto' | 'actividad' | 'correcciones' | 'memoria';
type Filtro = 'todo' | 'ia' | 'manual';

/** Cambios hechos por personas: ediciones a mano y restauraciones */
const esManual = (intent: string) => ['MANUAL', 'RESTAURAR'].includes((intent || '').toUpperCase());
type Lado = 'antes' | 'despues';
type Confirmacion = { tipo: 'reiniciar' } | { tipo: 'restaurar'; version: VersionDetalle; lado: Lado } | null;

const formatoHora = (ts: number) => {
  const d = new Date(ts * 1000);
  const hoy = new Date();
  const mismoDia = d.toDateString() === hoy.toDateString();
  const hora = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return mismoDia ? hora : `${d.toLocaleDateString([], { day: '2-digit', month: 'short' })} · ${hora}`;
};

const formatoTokens = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n));

/** "+A,B | ~C | -D" → chips. Filtra ids técnicos como antes hacía el modal. */
function chipsDelta(delta: string): Array<{ tipo: '+' | '~' | '-'; texto: string }> {
  if (!delta || delta === 'sin_cambios') return [];
  const chips: Array<{ tipo: '+' | '~' | '-'; texto: string }> = [];
  delta.split('|').map(p => p.trim()).forEach(parte => {
    const tipo = parte[0] as '+' | '~' | '-';
    if (!['+', '~', '-'].includes(tipo)) return;
    parte.slice(1).split(',').map(x => x.trim()).filter(Boolean)
      .filter(x => !/^node_\w+$/i.test(x) && !['diagrama', 'eliminadas', 'borradas'].includes(x.toLowerCase()))
      .forEach(texto => chips.push({ tipo, texto }));
  });
  return chips;
}

const ETIQUETA_LADO: Record<Lado, string> = { antes: 'Antes', despues: 'Después' };

/** Qué hizo el cambio, en palabras: "Manual", "Restaurado", "IA · Revisión"… */
const NOMBRES_INTENT: Record<string, string> = {
  IA: '', CREAR: 'Creación', MODIFICAR: 'Edición', REFACTOR: 'Refactor', REFACTORIZAR: 'Refactor',
  ELIMINAR: 'Eliminación', REVISAR: 'Revisión', LIMPIAR: 'Limpieza', OPTIMIZAR: 'Optimización',
  REQUISITOS: 'Requisitos', IMAGEN: 'Imagen', ROLES: 'Roles', TAREAS: 'Tareas', EXPLICAR: 'Explicación',
};
function etiquetaOrigen(intent: string): { texto: string; clase: 'ia' | 'manual' } {
  const i = (intent || '').toUpperCase();
  if (i === 'MANUAL') return { texto: 'Manual', clase: 'manual' };
  if (i === 'RESTAURAR') return { texto: 'Restaurado', clase: 'manual' };
  const nombre = i in NOMBRES_INTENT ? NOMBRES_INTENT[i] : i.charAt(0) + i.slice(1).toLowerCase();
  return { texto: nombre ? `IA · ${nombre}` : 'IA', clase: 'ia' };
}

export const ContextModal: React.FC<Props> = ({
  isOpen,
  onClose,
  contexto,
  onReiniciar,
  proyectoId,
  puedeRestaurar = false,
  onRestaurar,
  versionInicial = null,
  correccionesDiagrama,
}) => {
  const [pestana, setPestana] = useState<Pestana>('historial');
  const [filtro, setFiltro] = useState<Filtro>('todo');
  const [seleccion, setSeleccion] = useState<number | null>(null);
  const [lado, setLado] = useState<Lado>('antes');
  const [confirmacion, setConfirmacion] = useState<Confirmacion>(null);
  const [ocupado, setOcupado] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const [verTexto, setVerTexto] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const dialogoRef = useRef<HTMLDivElement>(null);

  const pid = proyectoId ?? contexto?.proyecto_id;
  const { versiones, hayMas, cargando, error, detalles, cargandoDetalle, cargarMas, cargarDetalle } =
    useVersionesContexto(pid, isOpen);

  const visibles = useMemo(
    () => versiones.filter(v => filtro === 'todo' || (filtro === 'manual') === esManual(v.intent)),
    [versiones, filtro]
  );

  // Abrir en la versión pedida (desde una propuesta del chat)
  useEffect(() => {
    if (isOpen && versionInicial) {
      setPestana('historial');
      setFiltro('todo');
      setSeleccion(versionInicial);
      setLado('antes');
    }
  }, [isOpen, versionInicial]);

  // Seleccionar la más reciente al abrir / cuando llega una nueva / al cambiar el filtro
  useEffect(() => {
    if (!isOpen) return;
    if (visibles.length && (seleccion === null || !visibles.some(v => v.id === seleccion))) {
      setSeleccion(visibles[0].id);
    }
  }, [isOpen, visibles, seleccion]);

  useEffect(() => {
    if (isOpen && seleccion !== null && !detalles[seleccion]) cargarDetalle(seleccion);
  }, [isOpen, seleccion, detalles, cargarDetalle]);

  // Esc cierra (primero la confirmación, si hay una)
  useEffect(() => {
    if (!isOpen) return;
    const alTeclado = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      e.stopPropagation();
      if (confirmacion) setConfirmacion(null);
      else onClose();
    };
    window.addEventListener('keydown', alTeclado);
    return () => window.removeEventListener('keydown', alTeclado);
  }, [isOpen, confirmacion, onClose]);

  useEffect(() => {
    if (isOpen) dialogoRef.current?.focus();
  }, [isOpen]);

  useEffect(() => {
    if (!aviso) return;
    const t = setTimeout(() => setAviso(null), 3500);
    return () => clearTimeout(t);
  }, [aviso]);

  const detalle = seleccion !== null ? detalles[seleccion] : undefined;
  const resumenSel = versiones.find(v => v.id === seleccion);

  const comparacion = useMemo(
    () => (detalle?.estado_antes && detalle?.estado_despues
      ? compararVersiones(detalle.estado_antes, detalle.estado_despues)
      : null),
    [detalle]
  );

  // Si la versión no tiene "después", mostrar el "antes"
  const ladoEfectivo: Lado = lado === 'despues' && !resumenSel?.tiene_despues ? 'antes' : lado;
  const estadoMostrado = detalle ? (ladoEfectivo === 'antes' ? detalle.estado_antes : detalle.estado_despues) : null;

  if (!isOpen) return null;

  const eventosMemoria = contexto?.historial_comprimido || [];
  const correcciones = correccionesDiagrama ?? contexto?.correcciones ?? [];
  const secciones = contexto?.memoria_secciones;
  const tokensAhorrados = contexto?.tokens_ahorrados_estimados || 0;
  const sinVersiones = !cargando && versiones.length === 0;

  const copiarTexto = () => {
    if (!contexto?.contexto_compilado_llm) return;
    navigator.clipboard.writeText(contexto.contexto_compilado_llm);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  const confirmar = async () => {
    if (!confirmacion) return;
    setOcupado(true);
    try {
      if (confirmacion.tipo === 'reiniciar') {
        await onReiniciar();
        setAviso('Memoria de la IA reiniciada. El historial de versiones se conserva.');
      } else if (onRestaurar) {
        const estado = confirmacion.lado === 'antes' ? confirmacion.version.estado_antes : confirmacion.version.estado_despues;
        if (estado) {
          await onRestaurar(estado, confirmacion.version, confirmacion.lado);
          setAviso('Versión restaurada en la pizarra de toda la sala.');
        }
      }
      setConfirmacion(null);
    } catch (e) {
      setAviso(e instanceof Error ? e.message : 'No se pudo completar la acción.');
    } finally {
      setOcupado(false);
    }
  };

  // ── Bloques de la pestaña Historial ──────────────────────────────────

  const listaVersiones = (
    <ul className="context-modal__timeline" aria-label="Historial de cambios">
      {visibles.length === 0 && (
        <li className="context-modal__nota context-modal__nota--centro">
          {filtro === 'manual' ? 'Todavía no hay cambios manuales.' : filtro === 'ia' ? 'Todavía no hay cambios hechos con la IA.' : 'Todavía no hay cambios.'}
        </li>
      )}
      {visibles.map(v => {
        const chips = chipsDelta(v.delta);
        const activa = v.id === seleccion;
        const origen = etiquetaOrigen(v.intent);
        return (
          <li key={v.id}>
            <button
              type="button"
              className={`context-modal__evento context-modal__evento--${origen.clase}${activa ? ' is-active' : ''}`}
              onClick={() => { setSeleccion(v.id); setLado('antes'); }}
              aria-current={activa ? 'true' : undefined}
            >
              <span className="context-modal__evento-meta">
                <span className={`context-modal__intent context-modal__intent--${origen.clase}`}>
                  {origen.texto}
                </span>
                <span>{formatoHora(v.ts)}</span>
                {v.autor && <span className="context-modal__autor">· {v.autor}</span>}
                {v.estado_propuesta && (
                  <span className={`context-modal__propuesta context-modal__propuesta--${v.estado_propuesta}`}>
                    {v.estado_propuesta === 'pendiente' ? 'Pendiente' : v.estado_propuesta === 'aprobada' ? 'Aprobada' : 'Rechazada'}
                  </span>
                )}
              </span>
              <span className="context-modal__evento-cmd">{v.cmd || 'Sin instrucción'}</span>
              {chips.length > 0 && (
                <span className="context-modal__chips">
                  {chips.slice(0, 6).map((c, i) => (
                    <span key={i} className={`context-modal__chip context-modal__chip--${c.tipo === '+' ? 'add' : c.tipo === '-' ? 'del' : 'mod'}`}>
                      {c.tipo === '-' ? '−' : c.tipo}{c.texto}
                    </span>
                  ))}
                </span>
              )}
            </button>
          </li>
        );
      })}
      {hayMas && (
        <li>
          <button type="button" className="context-modal__mas" onClick={cargarMas} disabled={cargando}>
            {cargando ? 'Cargando…' : 'Cargar interacciones anteriores'}
          </button>
        </li>
      )}
    </ul>
  );

  const listaLegada = (
    <div className="context-modal__legado">
      <p className="context-modal__nota">
        Estas interacciones son anteriores al historial de versiones: se ven en texto, pero no tienen versión guardada para previsualizar.
      </p>
      <ul className="context-modal__timeline">
        {eventosMemoria.slice().reverse().map((ev, i) => (
          <li key={i}>
            <div className="context-modal__evento is-static">
              <span className="context-modal__evento-meta">
                <span className={`context-modal__intent context-modal__intent--${etiquetaOrigen(ev.intent).clase}`}>{etiquetaOrigen(ev.intent).texto}</span>
                <span>{formatoHora(ev.ts)}</span>
              </span>
              <span className="context-modal__evento-cmd">{ev.cmd}</span>
              <span className="context-modal__evento-resumen">{ev.summary}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );

  const panelPreview = (
    <section className="context-modal__preview" aria-label="Versión del diagrama">
      {!resumenSel ? (
        <div className="context-modal__vacio">Selecciona una interacción para ver la versión del diagrama.</div>
      ) : (
        <>
          <header className="context-modal__preview-header">
            <div className="context-modal__preview-titulo">
              <span className="context-modal__eyebrow">
                {ladoEfectivo === 'antes' ? 'Versión anterior a' : 'Versión posterior a'}
                {resumenSel.autor ? ` · ${resumenSel.autor}` : ''}
              </span>
              <h4 title={resumenSel.cmd}>«{resumenSel.cmd || 'Sin instrucción'}»</h4>
            </div>
            <div className="context-modal__segmentado" role="group" aria-label="Versión a mostrar">
              {(['antes', 'despues'] as Lado[]).map(l => (
                <button
                  key={l}
                  type="button"
                  className={ladoEfectivo === l ? 'is-active' : ''}
                  onClick={() => setLado(l)}
                  disabled={(l === 'antes' && !resumenSel.tiene_antes) || (l === 'despues' && !resumenSel.tiene_despues)}
                  aria-pressed={ladoEfectivo === l}
                >
                  {ETIQUETA_LADO[l]}
                </button>
              ))}
            </div>
          </header>

          <div className="context-modal__lienzo">
            {cargandoDetalle === resumenSel.id && !detalle ? (
              <div className="context-modal__vacio">Cargando versión…</div>
            ) : !resumenSel.tiene_antes && !resumenSel.tiene_despues ? (
              <div className="context-modal__vacio">Esta interacción no guardó una versión del diagrama.</div>
            ) : (
              <DiagramPreview
                estado={estadoMostrado}
                comparacion={comparacion}
                lado={ladoEfectivo}
                vacioTexto={ladoEfectivo === 'antes' ? 'La pizarra estaba vacía antes de este cambio.' : 'La pizarra quedó vacía después de este cambio.'}
              />
            )}
          </div>

          {estadoMostrado && (estadoMostrado.nodes || []).length > 0 && (
            <div className="context-modal__exportar" role="group" aria-label="Exportar esta versión">
              <span>Exportar esta versión:</span>
              {(() => {
                const nombre = `version_${resumenSel.id}_${ladoEfectivo}`;
                const est = { nodes: estadoMostrado.nodes || [], relations: estadoMostrado.relations || [] };
                return (
                  <>
                    <button type="button" onClick={() => exportarPng(est, nombre).catch(() => {})}>PNG</button>
                    <button type="button" onClick={() => exportarSvg(est, nombre)}>SVG</button>
                    <button type="button" onClick={() => exportarPdf(est, nombre)}>PDF</button>
                  </>
                );
              })()}
            </div>
          )}

          {resumenSel.resumen && <p className="context-modal__resumen-ia">{resumenSel.resumen}</p>}

          {resumenSel.estado_propuesta && (
            <div className={`context-modal__decision context-modal__decision--${resumenSel.estado_propuesta}`}>
              <span><strong>Pedida por</strong> {resumenSel.autor || '—'}</span>
              <span>
                <strong>
                  {resumenSel.estado_propuesta === 'pendiente' ? 'Estado' : resumenSel.estado_propuesta === 'aprobada' ? 'Aprobada por' : 'Rechazada por'}
                </strong>{' '}
                {resumenSel.estado_propuesta === 'pendiente'
                  ? 'pendiente de aprobación'
                  : `${resumenSel.decidida_por || '—'}${resumenSel.decidida_en ? ` · ${formatoHora(resumenSel.decidida_en)}` : ''}`}
              </span>
            </div>
          )}

          {resumenSel.estado_propuesta && resumenSel.estado_propuesta !== 'aprobada' && detalle?.propuesta && (
            <div className="context-modal__cambios">
              <span className="context-modal__eyebrow">
                {resumenSel.estado_propuesta === 'pendiente' ? 'Lo que propone la IA' : 'Lo que propuso la IA (no se aplicó)'}
              </span>
              <ul className="context-modal__lista-cambios">
                {(detalle.propuesta.nodes || []).map((n: any, i: number) => (
                  <li key={`pn${i}`} className="context-modal__cambio context-modal__cambio--agregado">
                    <span className="context-modal__cambio-nombre">{n.name || n.nombre}</span>
                    {(n.attributes || n.atributos || []).length > 0 && (
                      <span className="context-modal__cambio-detalle">
                        {(n.attributes || n.atributos || []).slice(0, 12).map((a: any, j: number) => (
                          <code key={j}>{typeof a === 'string' ? a : `${a.nombre}: ${a.tipo}`}</code>
                        ))}
                      </span>
                    )}
                  </li>
                ))}
                {((detalle.propuesta as any).tareas || (detalle.propuesta as any).tasks || []).map((t: any, i: number) => (
                  <li key={`pt${i}`} className="context-modal__cambio context-modal__cambio--agregado">
                    <span className="context-modal__cambio-nombre">
                      {t.titulo || `Tarea ${i + 1}`}
                      <span className="context-modal__cambio-tipo">tarea · {t.area || t.tipo || 'general'}</span>
                    </span>
                  </li>
                ))}
                {((detalle.propuesta as any).roles || []).map((r: any, i: number) => (
                  <li key={`pr${i}`} className="context-modal__cambio context-modal__cambio--modificado">
                    <span className="context-modal__cambio-nombre">
                      {r.nombre} → {r.rol_ia || 'Desarrollador'}
                      <span className="context-modal__cambio-tipo">rol</span>
                    </span>
                    {(r.clases_asignadas || []).length > 0 && (
                      <span className="context-modal__cambio-detalle">
                        {r.clases_asignadas.map((c: string) => <code key={c}>{c}</code>)}
                      </span>
                    )}
                  </li>
                ))}
                {(detalle.propuesta.deletedNodes || []).map((d: any, i: number) => (
                  <li key={`pd${i}`} className="context-modal__cambio context-modal__cambio--eliminado">
                    <span className="context-modal__cambio-nombre">− {typeof d === 'string' ? d : d?.name || d?.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="context-modal__cambios">
            <span className="context-modal__eyebrow">Cambios</span>
            {!comparacion ? (
              <p className="context-modal__nota">
                {resumenSel.tiene_despues ? 'Cargando cambios…' : 'Aún no se registró cómo quedó la pizarra después de este cambio.'}
              </p>
            ) : comparacion.sinCambios ? (
              <p className="context-modal__nota">La pizarra no cambió (por ejemplo, una explicación o una consulta).</p>
            ) : (
              <ul className="context-modal__lista-cambios">
                {comparacion.nodos.map(n => (
                  <li key={n.id} className={`context-modal__cambio context-modal__cambio--${n.estado}`}>
                    <span className="context-modal__cambio-nombre">
                      {n.estado === 'agregado' ? '+ ' : n.estado === 'eliminado' ? '− ' : '~ '}
                      {n.renombradoDe ? `${n.renombradoDe} → ${n.nombre}` : n.nombre}
                      <span className="context-modal__cambio-tipo">
                        {n.estado === 'agregado' ? 'clase nueva' : n.estado === 'eliminado' ? 'clase eliminada' : 'modificada'}
                      </span>
                    </span>
                    {n.estado === 'modificado' && (
                      <span className="context-modal__cambio-detalle">
                        {[...n.atributos.agregados, ...n.metodos.agregados].map(s => <code key={`a${s}`} className="is-add">+ {s}</code>)}
                        {[...n.atributos.eliminados, ...n.metodos.eliminados].map(s => <code key={`e${s}`} className="is-del">− {s}</code>)}
                        {[...n.atributos.modificados, ...n.metodos.modificados].map(m => (
                          <code key={`m${m.antes}`} className="is-mod">{m.antes} → {m.despues}</code>
                        ))}
                      </span>
                    )}
                  </li>
                ))}
                {comparacion.relacionesAgregadas.map(r => (
                  <li key={`ra${r}`} className="context-modal__cambio context-modal__cambio--agregado">
                    <span className="context-modal__cambio-nombre">+ {r}<span className="context-modal__cambio-tipo">relación nueva</span></span>
                  </li>
                ))}
                {comparacion.relacionesEliminadas.map(r => (
                  <li key={`re${r}`} className="context-modal__cambio context-modal__cambio--eliminado">
                    <span className="context-modal__cambio-nombre">− {r}<span className="context-modal__cambio-tipo">relación eliminada</span></span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {onRestaurar && detalle && estadoMostrado && (
            <div className="context-modal__preview-acciones">
              {puedeRestaurar ? (
                <button
                  type="button"
                  className="context-modal__btn context-modal__btn--primario"
                  onClick={() => setConfirmacion({ tipo: 'restaurar', version: detalle, lado: ladoEfectivo })}
                >
                  Restaurar esta versión
                </button>
              ) : (
                <span className="context-modal__nota">Solo quienes tienen permiso de edición pueden restaurar versiones.</span>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <div className="context-modal__overlay" onClick={onClose}>
      <div
        ref={dialogoRef}
        className="context-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="context-modal-titulo"
        tabIndex={-1}
        onClick={e => e.stopPropagation()}
      >
        <header className="context-modal__header">
          <div className="context-modal__header-texto">
            <h3 id="context-modal-titulo">Historial del proyecto</h3>
            <p>{contexto?.dominio || 'Sistema de Software'}</p>
          </div>
          <div className="context-modal__metricas">
            <span className="context-modal__metrica"><strong>{versiones.length}{hayMas ? '+' : ''}</strong> cambios</span>
            {pestana === 'memoria' && (
              <span className="context-modal__metrica" title="Estimación: compara el tamaño de la memoria con el de enviar el chat completo">
                <strong>~{formatoTokens(tokensAhorrados)}</strong> tokens ahorrados (est.)
              </span>
            )}
          </div>
          <button type="button" className="context-modal__cerrar" onClick={onClose} aria-label="Cerrar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </header>

        <nav className="context-modal__tabs" role="tablist">
          {([
            ['historial', 'Cambios'],
            ['actividad', 'Actividad del equipo'],
            ['correcciones', `Correcciones${correcciones.length ? ` · ${correcciones.length}` : ''}`],
            ['proyecto', 'Memoria del proyecto'],
            ['memoria', 'Contexto de la IA'],
          ] as Array<[Pestana, string]>).map(([id, texto]) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={pestana === id}
              className={`context-modal__tab${pestana === id ? ' is-active' : ''}`}
              onClick={() => setPestana(id)}
            >
              {texto}
            </button>
          ))}
        </nav>

        <div className="context-modal__body">
          {pestana === 'historial' && (
            error && !versiones.length ? (
              <div className="context-modal__vacio">{error}</div>
            ) : sinVersiones ? (
              eventosMemoria.length ? listaLegada : (
                <div className="context-modal__vacio">
                  Todavía no hay cambios. Cada cambio en la pizarra (a mano o con @diag en el chat) se guardará aquí con la versión anterior del diagrama.
                </div>
              )
            ) : (
              <div className="context-modal__historial">
                <aside className="context-modal__lista">
                  <div className="context-modal__filtros" role="group" aria-label="Filtrar historial">
                    {([['todo', 'Todo'], ['ia', 'IA'], ['manual', 'Manual']] as Array<[Filtro, string]>).map(([id, texto]) => (
                      <button
                        key={id}
                        type="button"
                        className={filtro === id ? 'is-active' : ''}
                        aria-pressed={filtro === id}
                        onClick={() => setFiltro(id)}
                      >
                        {texto}
                        <span className="context-modal__filtro-n">
                          {id === 'todo' ? versiones.length : versiones.filter(v => (id === 'manual') === esManual(v.intent)).length}
                        </span>
                      </button>
                    ))}
                  </div>
                  {cargando && !versiones.length ? <div className="context-modal__vacio">Cargando historial…</div> : listaVersiones}
                </aside>
                {panelPreview}
              </div>
            )
          )}

          {pestana === 'actividad' && (
            pid ? <ContribucionPanel proyectoId={pid} onVerVersion={id => { setPestana('historial'); setFiltro('todo'); setSeleccion(id); setLado('antes'); }} /> : <div className="context-modal__vacio">Abre el modal desde una sala para ver la actividad.</div>
          )}

          {pestana === 'proyecto' && (
            pid ? (
              <MemoriaPanel proyectoId={pid} puedeEditar={puedeRestaurar} />
            ) : (
              <div className="context-modal__vacio">Abre el modal desde una sala para ver la memoria del proyecto.</div>
            )
          )}

          {pestana === 'correcciones' && (
            correcciones.length === 0 ? (
              <div className="context-modal__vacio">
                No hay correcciones. Para agregar una: selecciona una clase → Panel de propiedades → Correcciones.
                La IA recibe las abiertas en cada pedido.
              </div>
            ) : (
              <ul className="context-modal__correcciones">
                {correcciones.map((c, i) => (
                  <li key={c.id || i} className="context-modal__correccion">
                    <span className="context-modal__correccion-target">{c.target}</span>
                    <span className="context-modal__correccion-texto">{c.text}</span>
                    <span className={`context-modal__estado context-modal__estado--${c.estado === 'abierta' ? 'abierta' : 'resuelta'}`}>
                      {c.estado}
                    </span>
                  </li>
                ))}
              </ul>
            )
          )}

          {pestana === 'memoria' && (
            <div className="context-modal__memoria">
              <p className="context-modal__nota">
                Esto es lo que la IA recibe al inicio de cada pedido para recordar el proyecto, en lugar de todo el chat.
              </p>

              {!verTexto && secciones && (
                <div className="context-modal__secciones">
                  <section className="context-modal__seccion">
                    <h5>Dominio</h5>
                    <p>{secciones.dominio}</p>
                  </section>
                  <section className="context-modal__seccion context-modal__seccion--ancha">
                    <h5>
                      Memoria del proyecto
                      <span className="context-modal__contador">reglas fijas + las más relevantes para cada pedido</span>
                    </h5>
                    {!secciones.memorias?.length ? (
                      <p className="context-modal__nota">Todavía no hay memorias guardadas.</p>
                    ) : (
                      <ul className="context-modal__acciones">
                        {secciones.memorias.map((m, i) => (
                          <li key={i}>
                            <span className="context-modal__intent">{m.tipo}</span>
                            <span className="context-modal__accion-cmd"><code>{m.topic_key}</code> {m.que}</span>
                            {m.aprendido && <span className="context-modal__accion-resumen">→ {m.aprendido}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                  </section>
                  <section className="context-modal__seccion">
                    <h5>Resumen acumulado</h5>
                    <p>{secciones.resumen || <span className="context-modal__nota">Sin resumen todavía.</span>}</p>
                  </section>
                  <section className="context-modal__seccion context-modal__seccion--ancha">
                    <h5>
                      Últimas acciones
                      <span className="context-modal__contador">
                        {secciones.ultimas_acciones.length} de {eventosMemoria.length} en memoria
                      </span>
                    </h5>
                    {secciones.ultimas_acciones.length === 0 ? (
                      <p className="context-modal__nota">Ninguna.</p>
                    ) : (
                      <ol className="context-modal__acciones">
                        {secciones.ultimas_acciones.slice().reverse().map((a, i) => (
                          <li key={i}>
                            <span className="context-modal__intent">{a.intent}</span>
                            <span className="context-modal__accion-cmd">{a.cmd}</span>
                            <span className="context-modal__accion-resumen">{a.summary}</span>
                          </li>
                        ))}
                      </ol>
                    )}
                  </section>
                  <section className="context-modal__seccion context-modal__seccion--ancha">
                    <h5>
                      Correcciones pendientes
                      {secciones.total_correcciones_abiertas > secciones.correcciones_abiertas.length && (
                        <span className="context-modal__contador">
                          {secciones.correcciones_abiertas.length} de {secciones.total_correcciones_abiertas}
                        </span>
                      )}
                    </h5>
                    {secciones.correcciones_abiertas.length === 0 ? (
                      <p className="context-modal__nota">Ninguna.</p>
                    ) : (
                      <ul className="context-modal__acciones">
                        {secciones.correcciones_abiertas.map((c, i) => (
                          <li key={i}>
                            <span className="context-modal__correccion-target">{c.target}</span>
                            <span className="context-modal__accion-cmd">{c.text}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </section>
                  <section className="context-modal__seccion context-modal__seccion--ancha">
                    <h5>Diagrama actual (comprimido)</h5>
                    {secciones.diagrama_dsl
                      ? <code className="context-modal__dsl">{secciones.diagrama_dsl}</code>
                      : <p className="context-modal__nota">Aún no se envió el diagrama.</p>}
                  </section>
                </div>
              )}

              {(verTexto || !secciones) && (
                <pre className="context-modal__texto">{contexto?.contexto_compilado_llm || 'Sin memoria compilada activa.'}</pre>
              )}

              <div className="context-modal__memoria-acciones">
                {secciones && (
                  <button type="button" className="context-modal__btn" onClick={() => setVerTexto(v => !v)}>
                    {verTexto ? 'Ver por secciones' : 'Ver texto exacto'}
                  </button>
                )}
                <button type="button" className="context-modal__btn" onClick={copiarTexto}>
                  {copiado ? 'Copiado' : 'Copiar texto'}
                </button>
              </div>
            </div>
          )}
        </div>

        <footer className="context-modal__footer">
          {pestana === 'proyecto' || pestana === 'memoria' ? (
            <button type="button" className="context-modal__btn context-modal__btn--peligro" onClick={() => setConfirmacion({ tipo: 'reiniciar' })}>
              Reiniciar memoria de la IA
            </button>
          ) : <span />}
          {aviso && <span className="context-modal__aviso" role="status">{aviso}</span>}
          <button type="button" className="context-modal__btn context-modal__btn--primario" onClick={onClose}>
            Cerrar
          </button>
        </footer>

        {confirmacion && (
          <div className="context-modal__confirmar-fondo">
            <div className="context-modal__confirmar" role="alertdialog" aria-modal="true" aria-labelledby="context-modal-confirmar">
              <h4 id="context-modal-confirmar">
                {confirmacion.tipo === 'reiniciar' ? '¿Reiniciar la memoria de la IA?' : '¿Restaurar esta versión?'}
              </h4>
              <p>
                {confirmacion.tipo === 'reiniciar'
                  ? 'La IA olvidará el resumen, las últimas acciones y las correcciones de este proyecto. El historial de versiones del diagrama se conserva.'
                  : `La pizarra de toda la sala volverá a como estaba ${confirmacion.lado === 'antes' ? 'antes' : 'después'} de «${confirmacion.version.cmd}». No se borra el historial: la restauración queda registrada como una interacción nueva.`}
              </p>
              <div className="context-modal__confirmar-acciones">
                <button type="button" className="context-modal__btn" onClick={() => setConfirmacion(null)} disabled={ocupado}>
                  Cancelar
                </button>
                <button
                  type="button"
                  className={`context-modal__btn ${confirmacion.tipo === 'reiniciar' ? 'context-modal__btn--peligro-lleno' : 'context-modal__btn--primario'}`}
                  onClick={confirmar}
                  disabled={ocupado}
                >
                  {ocupado ? 'Procesando…' : confirmacion.tipo === 'reiniciar' ? 'Reiniciar' : 'Restaurar'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
