import React, { useEffect, useMemo, useState } from 'react';
import { BadgeCheck, Ban, Flag, Hourglass, Pencil, RotateCcw, Wrench, Zap, type LucideIcon } from 'lucide-react';
import { apiFetch } from '@/shared/lib/api';

interface Fila {
  nombre: string;
  cambios_pizarra: number;
  cambios_manuales: number;
  restauraciones: number;
  ia_aprobados: number;
  ia_rechazados: number;
  correcciones_senaladas: number;
  correcciones_resueltas: number;
  tareas_asignadas: number;
  tareas_completadas: number;
  horas_estimadas: number;
  horas_completadas: number;
  comentarios: number;
}

type TipoEvento =
  | 'manual' | 'restaurar' | 'ia_aprobada' | 'ia_rechazada' | 'ia_pendiente' | 'ia_directa'
  | 'correccion_senalada' | 'correccion_resuelta';

interface Evento {
  tipo: TipoEvento;
  quien: string | null;
  ts: number;
  version_id?: number;
  delta?: string;
  resumen?: string;
  pedido?: string;
  pedido_por?: string;
  clase?: string;
  texto?: string;
  senalada_por?: string;
}

interface Respuesta {
  miembros: Fila[];
  totales: Fila & { ia_pendientes: number };
  eventos: Evento[];
}

const PERIODOS = [
  { id: '7', texto: '7 días', query: 'dias=7' },
  { id: '30', texto: '30 días', query: 'dias=30' },
  { id: 'todo', texto: 'Todo', query: 'todo=true' },
];

const FILTROS: Array<{ id: string; texto: string; tipos: TipoEvento[] }> = [
  { id: '', texto: 'Todos los cambios', tipos: [] },
  { id: 'manual', texto: 'A mano', tipos: ['manual', 'restaurar'] },
  { id: 'ia', texto: 'IA aprobada', tipos: ['ia_aprobada', 'ia_directa'] },
  { id: 'ia_no', texto: 'IA rechazada o esperando', tipos: ['ia_rechazada', 'ia_pendiente'] },
  { id: 'corr', texto: 'Correcciones', tipos: ['correccion_senalada', 'correccion_resuelta'] },
];

const ICONO: Record<TipoEvento, LucideIcon> = {
  manual: Pencil,
  restaurar: RotateCcw,
  ia_aprobada: BadgeCheck,
  ia_directa: Zap,
  ia_rechazada: Ban,
  ia_pendiente: Hourglass,
  correccion_senalada: Flag,
  correccion_resuelta: Wrench,
};

const fecha = (ts: number) =>
  new Date(ts * 1000).toLocaleString('es', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

/** "+A,B | ~C | -D:realization" → [{signo:'+', texto:'agregó', nombres:['A','B']}, …] */
function leerDelta(delta?: string) {
  const etiqueta: Record<string, string> = { '+': 'agregó', '~': 'modificó', '-': 'quitó' };
  return (delta || '')
    .split('|')
    .map(p => p.trim())
    .filter(p => p && etiqueta[p[0]])
    .map(p => ({
      signo: p[0],
      texto: etiqueta[p[0]],
      nombres: [...new Set(
        p.slice(1).split(',').map(n => n.trim()).filter(Boolean)
          .map(n => (n.includes(':') ? `relación de ${n.split(':')[0]}` : n)),
      )],
    }))
    .filter(p => p.nombres.length);
}

const Quien: React.FC<{ n?: string | null }> = ({ n }) => <strong className="contribucion__nombre">{n || 'Alguien'}</strong>;

function Frase({ e }: { e: Evento }) {
  const mismo = !!e.pedido_por && e.pedido_por === e.quien;
  switch (e.tipo) {
    case 'manual': return <><Quien n={e.quien} /> editó la pizarra a mano</>;
    case 'restaurar': return <><Quien n={e.quien} /> restauró una versión anterior</>;
    case 'ia_aprobada':
      return <><Quien n={e.quien} /> aprobó un cambio de la IA{mismo ? ' que había pedido' : <> pedido por <Quien n={e.pedido_por} /></>}</>;
    case 'ia_directa': return <><Quien n={e.quien} /> aplicó un cambio de la IA <small>(antes de que existiera la aprobación)</small></>;
    case 'ia_rechazada':
      return <><Quien n={e.quien} /> rechazó un cambio de la IA{mismo ? ' que había pedido' : <> pedido por <Quien n={e.pedido_por} /></>} — no se aplicó</>;
    case 'ia_pendiente': return <>Cambio de la IA pedido por <Quien n={e.pedido_por} /> — nadie lo aprobó todavía</>;
    case 'correccion_senalada': return <><Quien n={e.quien} /> señaló una corrección en <em>{e.clase}</em></>;
    case 'correccion_resuelta':
      return <><Quien n={e.quien} /> resolvió la corrección de <em>{e.clase}</em>{e.senalada_por && e.senalada_por !== e.quien ? <> que señaló <Quien n={e.senalada_por} /></> : null}</>;
    default: return null;
  }
}

/** CU40: quién cambió la pizarra (a mano, aprobando a la IA o resolviendo correcciones). */
export const ContribucionPanel: React.FC<{ proyectoId: number; onVerVersion?: (id: number) => void }> = ({ proyectoId, onVerVersion }) => {
  const [periodo, setPeriodo] = useState('30');
  const [datos, setDatos] = useState<Respuesta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [miembro, setMiembro] = useState('');
  const [filtro, setFiltro] = useState('');

  useEffect(() => {
    let vigente = true;
    setError(null);
    const q = PERIODOS.find(p => p.id === periodo)?.query ?? 'dias=30';
    apiFetch<Respuesta>(`/api/ia/contexto/${proyectoId}/actividad?${q}`)
      .then(d => { if (vigente) setDatos(d); })
      .catch(e => { if (vigente) setError(e instanceof Error ? e.message : 'No se pudo cargar la actividad'); });
    return () => { vigente = false; };
  }, [proyectoId, periodo]);

  const eventos = useMemo(() => {
    const tipos = FILTROS.find(f => f.id === filtro)?.tipos ?? [];
    return (datos?.eventos || []).filter(e =>
      (!miembro || e.quien === miembro || e.pedido_por === miembro || e.senalada_por === miembro) &&
      (!tipos.length || tipos.includes(e.tipo)));
  }, [datos, miembro, filtro]);

  const n = (v: number) => v || '—';
  const frac = (a: number, b: number) => (b ? `${a} de ${b}` : '—');

  return (
    <div className="contribucion">
      <div className="memoria-panel__barra">
        <p className="context-modal__nota">Quién cambió la pizarra: a mano, aprobando cambios de la IA o resolviendo correcciones.</p>
        <div className="context-modal__segmentado" role="group" aria-label="Período">
          {PERIODOS.map(p => (
            <button key={p.id} type="button" className={periodo === p.id ? 'is-active' : ''} aria-pressed={periodo === p.id} onClick={() => setPeriodo(p.id)}>
              {p.texto}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="memoria-panel__error" role="alert">{error}</div>}
      {!datos && !error && <div className="context-modal__vacio">Cargando actividad…</div>}

      {datos && (
        <>
          {datos.totales.ia_pendientes > 0 && (
            <div className="contribucion__aviso" role="status">
              <Hourglass size={14} aria-hidden="true" />
              {datos.totales.ia_pendientes === 1
                ? 'Hay 1 cambio de la IA esperando que alguien lo apruebe o rechace.'
                : `Hay ${datos.totales.ia_pendientes} cambios de la IA esperando que alguien los apruebe o rechace.`}
            </div>
          )}

          {/* ── Quién cambió la pizarra ── */}
          <section className="contribucion__seccion" aria-labelledby="contrib-miembros">
            <h4 id="contrib-miembros" className="context-modal__eyebrow">Quién cambió la pizarra</h4>
            {!datos.miembros.length ? (
              <div className="context-modal__vacio">Nadie cambió la pizarra en este período.</div>
            ) : (
              <div className="contribucion__tabla-wrap">
                <table className="contribucion__tabla">
                  <thead>
                    <tr>
                      <th scope="col">Miembro</th>
                      <th scope="col" className="is-num">Cambios en la pizarra</th>
                      <th scope="col" className="is-num">A mano</th>
                      <th scope="col" className="is-num">IA que aprobó</th>
                      <th scope="col" className="is-num">IA que rechazó</th>
                      <th scope="col" className="is-num">Correcciones resueltas</th>
                      <th scope="col" className="is-num">Correcciones señaladas</th>
                      <th scope="col" className="is-num">Tareas hechas</th>
                      <th scope="col" className="is-num">Comentarios</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datos.miembros.map(f => (
                      <tr key={f.nombre} className={miembro === f.nombre ? 'is-sel' : ''}>
                        <th scope="row">
                          <button
                            type="button"
                            className="contribucion__miembro"
                            onClick={() => setMiembro(m => (m === f.nombre ? '' : f.nombre))}
                            aria-pressed={miembro === f.nombre}
                            title="Ver solo sus cambios"
                          >
                            {f.nombre}
                          </button>
                        </th>
                        <td className="is-num is-fuerte">{n(f.cambios_pizarra)}</td>
                        <td className="is-num">{n(f.cambios_manuales + f.restauraciones)}</td>
                        <td className="is-num">{n(f.ia_aprobados)}</td>
                        <td className="is-num">{n(f.ia_rechazados)}</td>
                        <td className="is-num">{n(f.correcciones_resueltas)}</td>
                        <td className="is-num">{n(f.correcciones_senaladas)}</td>
                        <td className="is-num">{frac(f.tareas_completadas, f.tareas_asignadas)}</td>
                        <td className="is-num">{n(f.comentarios)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="contribucion__leyenda">
              <strong>Cambios en la pizarra</strong> = a mano + cambios de la IA que aprobó + correcciones que resolvió.
              Un cambio de la IA cuenta para quien lo aprobó, porque es quien lo puso en la pizarra.
            </p>
          </section>

          {/* ── Línea de tiempo ── */}
          <section className="contribucion__seccion" aria-labelledby="contrib-tiempo">
            <h4 id="contrib-tiempo" className="context-modal__eyebrow">Qué cambió y quién</h4>
            {datos.eventos.length > 0 && (
              <div className="contribucion__filtros">
                <select value={miembro} onChange={e => setMiembro(e.target.value)} aria-label="Filtrar por miembro">
                  <option value="">Todos los miembros</option>
                  {datos.miembros.map(m => <option key={m.nombre} value={m.nombre}>{m.nombre}</option>)}
                </select>
                <select value={filtro} onChange={e => setFiltro(e.target.value)} aria-label="Filtrar por tipo de cambio">
                  {FILTROS.map(f => <option key={f.id} value={f.id}>{f.texto}</option>)}
                </select>
              </div>
            )}
            {!datos.eventos.length ? (
              <div className="context-modal__vacio">No hubo cambios en este período.</div>
            ) : !eventos.length ? (
              <div className="context-modal__vacio">Ningún cambio coincide con el filtro.</div>
            ) : (
              <ol className="contribucion__tiempo">
                {eventos.map((e, i) => {
                  const partes = leerDelta(e.delta);
                  const detalle = e.tipo.startsWith('correccion') ? e.texto : e.tipo.startsWith('ia') ? e.pedido : '';
                  return (
                    <li key={`${e.tipo}-${e.version_id ?? i}-${e.ts}`} className={`contribucion__evento contribucion__evento--${e.tipo}`}>
                      <span className="contribucion__evento-icono" aria-hidden="true">{React.createElement(ICONO[e.tipo], { size: 14 })}</span>
                      <div className="contribucion__evento-cuerpo">
                        <p className="contribucion__frase"><Frase e={e} /></p>
                        {detalle && <p className="contribucion__detalle">“{detalle}”</p>}
                        {partes.length > 0 && (
                          <div className="contribucion__delta">
                            {partes.map(p => (
                              <span key={p.signo} className={`contribucion__delta-${p.signo === '+' ? 'mas' : p.signo === '-' ? 'menos' : 'mod'}`}>
                                {p.texto} {p.nombres.join(', ')}
                              </span>
                            ))}
                          </div>
                        )}
                        <div className="contribucion__pie">
                          <time dateTime={new Date(e.ts * 1000).toISOString()}>{fecha(e.ts)}</time>
                          {onVerVersion && e.version_id && (
                            <button type="button" className="contribucion__ver" onClick={() => onVerVersion(e.version_id!)}>Ver en historial</button>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ol>
            )}
          </section>
        </>
      )}
    </div>
  );
};
