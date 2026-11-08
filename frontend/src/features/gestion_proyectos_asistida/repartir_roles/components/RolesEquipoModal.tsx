import React, { useState } from 'react';
import { useRepartirRoles } from '../hooks/useRepartirRoles';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  proyectoId: number;
}

export const RolesEquipoModal: React.FC<Props> = ({ isOpen, onClose, proyectoId }) => {
  const { roles, loading, error, repartirConIA, asignarManual } = useRepartirRoles(proyectoId);
  const [instrucciones, setInstrucciones] = useState('');
  const [editUserId, setEditUserId] = useState<number | null>(null);
  const [manualRol, setManualRol] = useState('');
  const [manualAreas, setManualAreas] = useState('');

  if (!isOpen) return null;

  const handleRepartir = async () => {
    await repartirConIA({ instrucciones: instrucciones.trim() || undefined });
  };

  const handleGuardarManual = async (usuarioId: number) => {
    if (!manualRol.trim()) return;
    const areasList = manualAreas
      .split(',')
      .map((a) => a.trim())
      .filter(Boolean);
    await asignarManual({
      usuario_id: usuarioId,
      rol_ia: manualRol.trim(),
      areas: areasList,
    });
    setEditUserId(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col text-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">
                Asignación Estructurada de Roles
              </h2>
              <p className="text-xs text-slate-400">
                Distribución inteligente de especialidades y responsabilidades técnicas
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

        {/* Toolbar con Prompt IA */}
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/20 flex items-center gap-3">
          <input
            type="text"
            placeholder="Instrucciones adicionales para la IA (opcional)..."
            value={instrucciones}
            onChange={(e) => setInstrucciones(e.target.value)}
            className="flex-1 bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handleRepartir}
            disabled={loading}
            className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-sm flex items-center gap-2 transition-colors"
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
            <span>Repartir con IA</span>
          </button>
        </div>

        {/* Lista de Colaboradores y Roles */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {error && (
            <div className="p-3 bg-red-950/50 border border-red-800/50 rounded-lg text-xs text-red-300 flex items-center gap-2">
              <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {roles.length === 0 && !loading && (
            <div className="text-center py-12 text-slate-500 text-xs">
              No hay colaboradores registrados o roles asignados aún.
            </div>
          )}

          {roles.map((c) => (
            <div
              key={c.usuario_id}
              className="p-4 bg-slate-800/40 border border-slate-700/50 rounded-lg hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-white text-sm">{c.nombre}</span>
                    {c.rol_ia ? (
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {c.rol_ia}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-700/60 text-slate-400">
                        Sin rol asignado
                      </span>
                    )}
                  </div>

                  {c.areas && c.areas.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {c.areas.map((area, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[10px] bg-slate-700/50 text-slate-300"
                        >
                          {area}
                        </span>
                      ))}
                    </div>
                  )}

                  {c.responsabilidades && c.responsabilidades.length > 0 && (
                    <ul className="text-xs text-slate-400 space-y-0.5 list-disc list-inside">
                      {c.responsabilidades.map((resp, idx) => (
                        <li key={idx}>{resp}</li>
                      ))}
                    </ul>
                  )}
                </div>

                <button
                  onClick={() => {
                    setEditUserId(c.usuario_id);
                    setManualRol(c.rol_ia || '');
                    setManualAreas((c.areas || []).join(', '));
                  }}
                  className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-700/50 transition-colors"
                  title="Editar rol manualmente"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
              </div>

              {editUserId === c.usuario_id && (
                <div className="mt-3 pt-3 border-t border-slate-700/60 flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Título de Rol (ej. Arquitecto Backend)"
                    value={manualRol}
                    onChange={(e) => setManualRol(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200"
                  />
                  <input
                    type="text"
                    placeholder="Áreas separadas por coma"
                    value={manualAreas}
                    onChange={(e) => setManualAreas(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200"
                  />
                  <button
                    onClick={() => handleGuardarManual(c.usuario_id)}
                    className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium"
                  >
                    Guardar
                  </button>
                  <button
                    onClick={() => setEditUserId(null)}
                    className="px-2 py-1 text-slate-400 hover:text-white text-xs"
                  >
                    Cancelar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

