import React, { useState, useEffect } from 'react';
import { getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import {
  generarTareasEquipo,
  obtenerTodasLasTareas,
  type TareaIA,
  type HabilidadDesarrollador,
} from '../../services/equipoService';
import './GestorEquipoIA.css';

interface ColaboradorInput {
  usuario_id: number;
  nombre: string;
  etiquetasRaw: string;
}

interface Props {
  proyectoId: number;
  descripcionProyecto: string;
  colaboradoresIniciales?: { usuario_id: number; nombre: string }[];
}

export const GestorEquipoIA: React.FC<Props> = ({
  proyectoId,
  descripcionProyecto,
  colaboradoresIniciales = [],
}) => {
  const currentIdentity = getUserIdentity();
  const currentUserName = currentIdentity.nickname || localStorage.getItem('usuario_nombre') || 'Mi Usuario';

  const [devs, setDevs] = useState<ColaboradorInput[]>(() => {
    if (colaboradoresIniciales.length > 0) {
      return colaboradoresIniciales.map(c => ({ ...c, etiquetasRaw: '' }));
    }
    return [{ usuario_id: 1, nombre: currentUserName, etiquetasRaw: 'backend, modelado' }];
  });

  useEffect(() => {
    if (colaboradoresIniciales && colaboradoresIniciales.length > 0) {
      setDevs(prev => {
        const existingNames = new Set(prev.map(d => d.nombre.toLowerCase()));
        const toAdd = colaboradoresIniciales
          .filter(c => !existingNames.has(c.nombre.toLowerCase()))
          .map(c => ({ usuario_id: c.usuario_id, nombre: c.nombre, etiquetasRaw: '' }));
        if (toAdd.length > 0) {
          return [...prev, ...toAdd];
        }
        return prev;
      });
    }
  }, [colaboradoresIniciales]);

  const [nuevoDevNombre, setNuevoDevNombre] = useState('');
  const [tareas, setTareas] = useState<TareaIA[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generado, setGenerado] = useState(false);
  const [tabIndex, setTabIndex] = useState<'pendientes' | 'historial'>('pendientes');

  const actualizarEtiqueta = (idx: number, value: string) => {
    setDevs(prev => prev.map((d, i) => (i === idx ? { ...d, etiquetasRaw: value } : d)));
  };

  const agregarColaborador = (nombre: string) => {
    const trimmed = nombre.trim();
    if (!trimmed) return;
    const exists = devs.some(d => d.nombre.toLowerCase() === trimmed.toLowerCase());
    if (exists) return;
    const nextId = devs.length > 0 ? Math.max(...devs.map(d => d.usuario_id)) + 1 : 1;
    setDevs(prev => [...prev, { usuario_id: nextId, nombre: trimmed, etiquetasRaw: '' }]);
    setNuevoDevNombre('');
  };

  const agregarmeAMi = () => {
    agregarColaborador(currentUserName);
  };

  const eliminarColaborador = (idx: number) => {
    setDevs(prev => prev.filter((_, i) => i !== idx));
  };

  const handleGenerar = async () => {
    setError('');
    setLoading(true);
    try {
      const desarrolladores: HabilidadDesarrollador[] = devs.map(d => ({
        usuario_id: d.usuario_id,
        nombre: d.nombre,
        etiquetas: d.etiquetasRaw.split(',').map(e => e.trim()).filter(Boolean),
      }));

      const resultado = await generarTareasEquipo({
        proyecto_id: proyectoId,
        descripcion_proyecto: descripcionProyecto,
        desarrolladores,
      });
      setTareas(resultado);
      setGenerado(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const handleVerProgreso = async () => {
    setLoading(true);
    try {
      const data = await obtenerTodasLasTareas(proyectoId);
      setTareas(data);
      setGenerado(true);
    } catch {
      setError('No hay tareas generadas para este proyecto.');
    } finally {
      setLoading(false);
    }
  };

  const tareasPorUsuario = tareas.reduce<Record<number, TareaIA[]>>((acc, t) => {
    if (!acc[t.usuario_id]) acc[t.usuario_id] = [];
    acc[t.usuario_id].push(t);
    return acc;
  }, {});

  return (
    <div className="gestor-equipo">
      <div className="gestor-equipo__header">
        <div className="gestor-equipo__icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
          </svg>
        </div>
        <div>
          <span className="gestor-equipo__title">GESTOR DE EQUIPO IA</span>
          <span className="gestor-equipo__sub">Reparte tareas y reduce el estrés del equipo</span>
        </div>
      </div>

      {error && <div className="gestor-equipo__error">{error}</div>}

      <div className="gestor-equipo__devs">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span className="gestor-equipo__section-label" style={{ margin: 0 }}>HABILIDADES DEL EQUIPO</span>
          {!devs.some(d => d.nombre.toLowerCase() === currentUserName.toLowerCase()) && (
            <button
              type="button"
              onClick={agregarmeAMi}
              style={{
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid var(--primary)',
                color: 'var(--primary)',
                borderRadius: '4px',
                padding: '2px 8px',
                fontSize: '11px',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              + Agregarme a mí
            </button>
          )}
        </div>

        {devs.map((d, idx) => (
          <div key={d.usuario_id} className="gestor-equipo__dev-row" style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="gestor-equipo__dev-name" style={{ minWidth: '90px', fontWeight: 600 }}>{d.nombre}</span>
              <input
                id={`input-etiquetas-${d.usuario_id}`}
                className="gestor-equipo__dev-input"
                placeholder="backend, modelado, frontend..."
                value={d.etiquetasRaw}
                onChange={e => actualizarEtiqueta(idx, e.target.value)}
                style={{ flex: 1 }}
              />
              {devs.length > 1 && (
                <button
                  type="button"
                  onClick={() => eliminarColaborador(idx)}
                  title="Quitar colaborador"
                  style={{ background: 'none', border: 'none', color: '#e53e3e', cursor: 'pointer', fontSize: '14px', padding: '0 4px' }}
                >
                  ×
                </button>
              )}
            </div>
            <div style={{ display: 'flex', gap: '4px', marginLeft: '98px', flexWrap: 'wrap' }}>
              {['backend', 'frontend', 'database', 'qa', 'modelado', 'seguridad'].map(tag => {
                const tagsList = d.etiquetasRaw.split(',').map(t => t.trim().toLowerCase());
                const already = tagsList.includes(tag);
                return (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => {
                      if (!already) {
                        const current = d.etiquetasRaw.trim();
                        const next = current ? `${current}, ${tag}` : tag;
                        actualizarEtiqueta(idx, next);
                      }
                    }}
                    disabled={already}
                    style={{
                      background: already ? 'transparent' : 'rgba(37,211,102,0.1)',
                      border: '1px dashed ' + (already ? 'var(--border-color)' : '#25D366'),
                      color: already ? 'var(--text-secondary)' : '#25D366',
                      borderRadius: '8px',
                      padding: '1px 5px',
                      fontSize: '9.5px',
                      cursor: already ? 'default' : 'pointer'
                    }}
                  >
                    + {tag}
                  </button>
                );
              })}
            </div>
          </div>
        ))}

        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
          <input
            type="text"
            placeholder="Nombre de otro desarrollador..."
            value={nuevoDevNombre}
            onChange={e => setNuevoDevNombre(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && agregarColaborador(nuevoDevNombre)}
            style={{
              flex: 1,
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '6px 10px',
              color: 'var(--text-primary)',
              fontSize: '12px'
            }}
          />
          <button
            type="button"
            onClick={() => agregarColaborador(nuevoDevNombre)}
            disabled={!nuevoDevNombre.trim()}
            style={{
              background: 'var(--surface-color)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              padding: '0 12px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '12px'
            }}
          >
            + Añadir
          </button>
        </div>
      </div>

      <div className="gestor-equipo__actions">
        <button
          id="btn-generar-equipo-ia"
          className="gestor-equipo__btn-primary"
          onClick={handleGenerar}
          disabled={loading}
        >
          {loading ? 'Generando...' : 'Generar Tareas con IA'}
        </button>
        <button
          id="btn-ver-progreso-equipo"
          className="gestor-equipo__btn-secondary"
          onClick={handleVerProgreso}
          disabled={loading}
        >
          {generado ? 'Refrescar' : 'Ver Progreso'}
        </button>
      </div>

      {generado && Object.keys(tareasPorUsuario).length > 0 && (
        <div className="gestor-equipo__resultado">
          <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
            <button 
              className={`gestor-equipo__tab ${tabIndex === 'pendientes' ? 'active' : ''}`}
              onClick={() => setTabIndex('pendientes')}
              style={{ flex: 1, padding: '6px', background: tabIndex === 'pendientes' ? 'var(--primary)' : 'var(--surface-color)', color: tabIndex === 'pendientes' ? 'var(--bg-color)' : 'var(--text-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 600 }}
            >
              TAREAS PENDIENTES
            </button>
            <button 
              className={`gestor-equipo__tab ${tabIndex === 'historial' ? 'active' : ''}`}
              onClick={() => setTabIndex('historial')}
              style={{ flex: 1, padding: '6px', background: tabIndex === 'historial' ? 'var(--primary)' : 'var(--surface-color)', color: tabIndex === 'historial' ? 'var(--bg-color)' : 'var(--text-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 600 }}
            >
              HISTORIAL
            </button>
          </div>
          {devs.map(d => {
            const allTs = tareasPorUsuario[d.usuario_id] ?? [];
            if (allTs.length === 0) return null;
            const ts = allTs.filter(t => tabIndex === 'historial' ? t.completada : !t.completada);
            if (ts.length === 0 && tabIndex === 'pendientes') return null; // Skip if no pending
            
            const hechas = allTs.filter(t => t.completada).length;
            const pct = allTs.length > 0 ? Math.round((hechas / allTs.length) * 100) : 0;
            return (
              <div key={d.usuario_id} className="gestor-equipo__dev-card">
                <div className="gestor-equipo__dev-card-header">
                  <span className="gestor-equipo__dev-card-name">{d.nombre}</span>
                  <span className="gestor-equipo__dev-card-pct">{pct}%</span>
                </div>
                <div className="gestor-equipo__bar-wrap">
                  <div className="gestor-equipo__bar" style={{ width: `${pct}%` }} />
                </div>
                <div className="gestor-equipo__tareas-list">
                  {ts.map(t => (
                    <div key={t.id} className={`gestor-equipo__tarea ${t.completada ? 'gestor-equipo__tarea--done' : ''}`}>
                      <span className={`gestor-equipo__tarea-tipo gestor-equipo__tarea-tipo--${t.tipo}`}>
                        {t.tipo === 'diagrama' ? 'UML' : 'DEV'}
                      </span>
                      <span className="gestor-equipo__tarea-titulo">{t.titulo}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
