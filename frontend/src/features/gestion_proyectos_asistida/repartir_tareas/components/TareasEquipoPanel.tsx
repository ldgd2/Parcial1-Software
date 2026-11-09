import React, { useState } from 'react';
import { etiquetaEsfuerzo } from '@/shared/utils/esfuerzo';
import { useTareasEquipo } from '../hooks/useTareasEquipo';

interface Props {
  proyectoId: number;
  isOpen: boolean;
  onClose: () => void;
  currentUserId?: number;
}

export const TareasEquipoPanel: React.FC<Props> = ({
  proyectoId,
  isOpen,
  onClose,
  currentUserId,
}) => {
  const { tareas, loading, error, repartirConIA, toggleTarea, crearManual, eliminar } =
    useTareasEquipo(proyectoId);

  const [filtro, setFiltro] = useState<'todas' | 'mis_tareas' | 'pendientes' | 'completadas'>('todas');
  const [nuevaTitulo, setNuevaTitulo] = useState('');
  const [nuevoArea, setNuevoArea] = useState('desarrollo');

  if (!isOpen) return null;

  const tareasFiltradas = tareas.filter((t) => {
    if (filtro === 'mis_tareas' && currentUserId) {
      return t.usuario_id === currentUserId;
    }
    if (filtro === 'pendientes') return !t.completada;
    if (filtro === 'completadas') return t.completada;
    return true;
  });

  const handleCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevaTitulo.trim() || !currentUserId) return;
    await crearManual({
      usuario_id: currentUserId,
      titulo: nuevaTitulo.trim(),
      area: nuevoArea,
    });
    setNuevaTitulo('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col text-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">
                Repartición de Tareas mediante IA
              </h2>
              <p className="text-xs text-slate-400">
                Planificación estructurada de actividades del proyecto por desarrollador
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800/60 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Filters and Actions Bar */}
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/20 flex flex-wrap items-center justify-between gap-4">
          <div className="flex bg-slate-800/70 p-0.5 rounded-lg border border-slate-700/60">
            {(
              [
                ['todas', 'Todas'],
                ['mis_tareas', 'Mis Tareas'],
                ['pendientes', 'Pendientes'],
                ['completadas', 'Completadas'],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setFiltro(key)}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                  filtro === key
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={() => repartirConIA({})}
            disabled={loading}
            className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 disabled:opacity-50 rounded-lg shadow-sm flex items-center gap-2 transition-colors"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            )}
            <span>Generar Tareas con IA</span>
          </button>
        </div>

        {/* Task List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2">
          {error && (
            <div className="p-3 bg-red-950/50 border border-red-800/50 rounded-lg text-xs text-red-300 flex items-center gap-2">
              <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {tareasFiltradas.length === 0 && !loading && (
            <div className="text-center py-12 text-slate-500 text-xs">
              No se encontraron tareas registradas con el filtro actual.
            </div>
          )}

          {tareasFiltradas.map((tarea) => (
            <div
              key={tarea.id}
              className={`p-3 rounded-lg border flex items-center justify-between gap-4 transition-all ${
                tarea.completada
                  ? 'bg-slate-900/40 border-slate-800/60 text-slate-500'
                  : 'bg-slate-800/50 border-slate-700/60 text-slate-200 hover:border-slate-600'
              }`}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <input
                  type="checkbox"
                  checked={tarea.completada}
                  onChange={(e) => toggleTarea(tarea.id, e.target.checked)}
                  className="w-4 h-4 rounded border-slate-700 text-teal-600 focus:ring-teal-500 bg-slate-900 cursor-pointer"
                />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-medium truncate ${
                        tarea.completada ? 'line-through text-slate-500' : 'text-slate-100'
                      }`}
                    >
                      {tarea.titulo}
                      {etiquetaEsfuerzo(tarea) && <small style={{ marginLeft: 6, opacity: 0.7 }}>({etiquetaEsfuerzo(tarea)})</small>}
                    </span>
                    {tarea.area && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-700/60 text-slate-300 shrink-0 uppercase tracking-wider">
                        {tarea.area}
                      </span>
                    )}
                  </div>
                  {tarea.descripcion && (
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {tarea.descripcion}
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={() => eliminar(tarea.id)}
                className="text-slate-500 hover:text-red-400 p-1.5 rounded transition-colors"
                title="Eliminar tarea"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Footer with Manual Create */}
        {currentUserId && (
          <form
            onSubmit={handleCrear}
            className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex items-center gap-3"
          >
            <input
              type="text"
              placeholder="Nueva tarea manual..."
              value={nuevaTitulo}
              onChange={(e) => setNuevaTitulo(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
            <select
              value={nuevoArea}
              onChange={(e) => setNuevoArea(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
            >
              <option value="desarrollo">Desarrollo</option>
              <option value="backend">Backend</option>
              <option value="frontend">Frontend</option>
              <option value="modelado">Modelado</option>
              <option value="testing">Testing</option>
            </select>
            <button
              type="submit"
              disabled={!nuevaTitulo.trim()}
              className="px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              Agregar
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

