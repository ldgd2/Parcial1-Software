import React, { useCallback, useEffect, useMemo, useState } from 'react';
import type { MemoriaItem } from '../types';
import {
  listarMemorias,
  crearMemoria,
  editarMemoria,
  eliminarMemoria,
  resolverConflictoMemoria,
} from '../services/contextoService';
import { EVENTO_VERSIONES_ACTUALIZADAS } from '../hooks/useVersionesContexto';

/** Se emite al crear / cambiar una memoria (p. ej. con /recordar en el chat). */
export const EVENTO_MEMORIA_ACTUALIZADA = 'contexto_ia_memoria_actualizada';

interface Props {
  proyectoId: number;
  autor?: string;
  /** Edición y borrado (en la sala: permiso de edición) */
  puedeEditar?: boolean;
}

const ETIQUETA_TIPO: Record<string, string> = {
  restriccion: 'Regla',
  convencion: 'Convención',
  decision: 'Decisión',
  correccion: 'Corrección',
  rechazo: 'Rechazo',
};
const ORDEN_TIPO = ['restriccion', 'convencion', 'decision', 'correccion', 'rechazo'];
const ETIQUETA_ORIGEN: Record<string, string> = {
  manual: 'escrita a mano',
  aprobacion: 'de una propuesta aprobada',
  rechazo: 'de una propuesta rechazada',
};

const fecha = (ts: number) => (ts ? new Date(ts * 1000).toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');

/** Memoria del proyecto (estilo Engram): lo que la IA recuerda y debe respetar. */
export const MemoriaPanel: React.FC<Props> = ({ proyectoId, autor, puedeEditar = true }) => {
  const [memorias, setMemorias] = useState<MemoriaItem[]>([]);
  const [conHistorial, setConHistorial] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nuevo, setNuevo] = useState('');
  const [editando, setEditando] = useState<number | null>(null);
  const [borrador, setBorrador] = useState<{ titulo: string; que: string; aprendido: string }>({ titulo: '', que: '', aprendido: '' });
  const [confirmarBorrar, setConfirmarBorrar] = useState<number | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setMemorias(await listarMemorias(proyectoId, conHistorial));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar la memoria');
    } finally {
      setCargando(false);
    }
  }, [proyectoId, conHistorial]);

  useEffect(() => { cargar(); }, [cargar]);
  useEffect(() => {
    const recargar = () => cargar();
    window.addEventListener(EVENTO_MEMORIA_ACTUALIZADA, recargar);
    window.addEventListener(EVENTO_VERSIONES_ACTUALIZADAS, recargar);   // aprobar / rechazar crea memorias
    return () => {
      window.removeEventListener(EVENTO_MEMORIA_ACTUALIZADA, recargar);
      window.removeEventListener(EVENTO_VERSIONES_ACTUALIZADAS, recargar);
    };
  }, [cargar]);

  const grupos = useMemo(() => {
    const g: Record<string, MemoriaItem[]> = {};
    memorias.forEach(m => { (g[m.tipo] ||= []).push(m); });
    return ORDEN_TIPO.filter(t => g[t]?.length).map(t => [t, g[t]] as const);
  }, [memorias]);
  const conflictos = memorias.filter(m => m.vigente && m.en_conflicto).length;

  const ejecutar = async (accion: () => Promise<unknown>) => {
    setError(null);
    try {
      await accion();
      await cargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo completar la acción');
    }
  };

  const agregar = (e: React.FormEvent) => {
    e.preventDefault();
    const texto = nuevo.trim();
    if (!texto) return;
    ejecutar(async () => {
      await crearMemoria(proyectoId, { texto, autor: autor ?? null });
      setNuevo('');
    });
  };

  return (
    <div className="memoria-panel">
      <p className="context-modal__nota">
        Lo que la IA recuerda del proyecto. Las <strong>reglas</strong> y <strong>convenciones</strong> se envían siempre; el resto se elige según
        cada pedido. Las decisiones y rechazos se guardan solos al aprobar o rechazar propuestas.
      </p>

      {puedeEditar && (
        <form className="memoria-panel__nuevo" onSubmit={agregar}>
          <input
            value={nuevo}
            onChange={e => setNuevo(e.target.value)}
            placeholder="Ej.: los ids son UUID   ·   entidades/cliente: el email es único   ·   nunca borrar Cliente"
            aria-label="Nueva memoria"
          />
          <button type="submit" className="context-modal__btn context-modal__btn--primario" disabled={!nuevo.trim()}>
            Recordar
          </button>
        </form>
      )}

      <div className="memoria-panel__barra">
        <span className="context-modal__nota">
          {memorias.filter(m => m.vigente).length} memorias vigentes
          {conflictos > 0 && <> · <strong className="memoria-panel__alerta">{conflictos} en conflicto</strong></>}
        </span>
        <label className="memoria-panel__check">
          <input type="checkbox" checked={conHistorial} onChange={e => setConHistorial(e.target.checked)} />
          Ver reemplazadas
        </label>
      </div>

      {error && <div className="memoria-panel__error" role="alert">{error}</div>}
      {cargando && !memorias.length && <div className="context-modal__vacio">Cargando memoria…</div>}
      {!cargando && !memorias.length && (
        <div className="context-modal__vacio">
          Todavía no hay memorias. Se crean al aprobar o rechazar propuestas, o con /recordar en el chat.
        </div>
      )}

      {grupos.map(([tipo, items]) => (
        <section key={tipo} className="memoria-panel__grupo">
          <h5>{ETIQUETA_TIPO[tipo] ?? tipo} <span className="context-modal__contador">{items.length}</span></h5>
          <ul className="memoria-panel__lista">
            {items.map(m => (
              <li
                key={m.id}
                className={`memoria-panel__item memoria-panel__item--${m.tipo}${m.vigente ? '' : ' is-reemplazada'}${m.en_conflicto ? ' is-conflicto' : ''}`}
              >
                {editando === m.id ? (
                  <form
                    className="memoria-panel__editar"
                    onSubmit={e => {
                      e.preventDefault();
                      ejecutar(async () => {
                        await editarMemoria(proyectoId, m.id, borrador);
                        setEditando(null);
                      });
                    }}
                  >
                    <input value={borrador.titulo} onChange={e => setBorrador(b => ({ ...b, titulo: e.target.value }))} aria-label="Título" />
                    <textarea value={borrador.que} onChange={e => setBorrador(b => ({ ...b, que: e.target.value }))} rows={3} aria-label="Qué" />
                    <textarea
                      value={borrador.aprendido}
                      onChange={e => setBorrador(b => ({ ...b, aprendido: e.target.value }))}
                      rows={2}
                      placeholder="Qué debe tener en cuenta la IA"
                      aria-label="Aprendido"
                    />
                    <div className="memoria-panel__acciones">
                      <button type="button" className="context-modal__btn" onClick={() => setEditando(null)}>Cancelar</button>
                      <button type="submit" className="context-modal__btn context-modal__btn--primario">Guardar</button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="memoria-panel__cabecera">
                      <code className="memoria-panel__tema">{m.topic_key}</code>
                      {!m.vigente && <span className="memoria-panel__marca">reemplazada</span>}
                      {m.en_conflicto && <span className="memoria-panel__marca memoria-panel__marca--conflicto">en conflicto</span>}
                    </div>
                    <div className="memoria-panel__titulo">{m.titulo}</div>
                    {m.que && m.que !== m.titulo && <div className="memoria-panel__texto">{m.que}</div>}
                    {m.aprendido && <div className="memoria-panel__aprendido">→ {m.aprendido}</div>}
                    {m.por_que && <div className="memoria-panel__meta">{m.por_que}</div>}
                    <div className="memoria-panel__meta">
                      {ETIQUETA_ORIGEN[m.origen] ?? m.origen}{m.autor ? ` · ${m.autor}` : ''} · {fecha(m.actualizada)}
                    </div>

                    {m.en_conflicto && m.vigente && puedeEditar && (
                      <div className="memoria-panel__conflicto">
                        <span>Esta memoria reemplazó a una escrita a mano. ¿Cuál vale?</span>
                        <div className="memoria-panel__acciones">
                          <button type="button" className="context-modal__btn" onClick={() => ejecutar(() => resolverConflictoMemoria(proyectoId, m.id, false))}>
                            Volver a la anterior
                          </button>
                          <button type="button" className="context-modal__btn context-modal__btn--primario" onClick={() => ejecutar(() => resolverConflictoMemoria(proyectoId, m.id, true))}>
                            Quedarse con esta
                          </button>
                        </div>
                      </div>
                    )}

                    {m.vigente && puedeEditar && !m.en_conflicto && (
                      <div className="memoria-panel__acciones">
                        {confirmarBorrar === m.id ? (
                          <>
                            <span className="context-modal__nota">¿Borrar esta memoria?</span>
                            <button type="button" className="context-modal__btn" onClick={() => setConfirmarBorrar(null)}>No</button>
                            <button
                              type="button"
                              className="context-modal__btn context-modal__btn--peligro"
                              onClick={() => ejecutar(async () => { await eliminarMemoria(proyectoId, m.id); setConfirmarBorrar(null); })}
                            >
                              Sí, borrar
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="context-modal__btn"
                              onClick={() => { setEditando(m.id); setBorrador({ titulo: m.titulo, que: m.que, aprendido: m.aprendido }); }}
                            >
                              Editar
                            </button>
                            <button type="button" className="context-modal__btn context-modal__btn--peligro" onClick={() => setConfirmarBorrar(m.id)}>
                              Borrar
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
};
