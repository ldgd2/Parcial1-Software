import React, { useState } from 'react';
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
  const [devs, setDevs] = useState<ColaboradorInput[]>(
    colaboradoresIniciales.map(c => ({ ...c, etiquetasRaw: '' }))
  );
  const [tareas, setTareas] = useState<TareaIA[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generado, setGenerado] = useState(false);
  const [tabIndex, setTabIndex] = useState<'pendientes' | 'historial'>('pendientes');

  const actualizarEtiqueta = (idx: number, value: string) => {
    setDevs(prev => prev.map((d, i) => (i === idx ? { ...d, etiquetasRaw: value } : d)));
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

      {devs.length > 0 && (
        <div className="gestor-equipo__devs">
          <span className="gestor-equipo__section-label">HABILIDADES DEL EQUIPO</span>
          {devs.map((d, idx) => (
            <div key={d.usuario_id} className="gestor-equipo__dev-row">
              <span className="gestor-equipo__dev-name">{d.nombre}</span>
              <input
                id={`input-etiquetas-${d.usuario_id}`}
                className="gestor-equipo__dev-input"
                placeholder="backend, modelado, frontend..."
                value={d.etiquetasRaw}
                onChange={e => actualizarEtiqueta(idx, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}

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
