import React, { useEffect } from 'react';
import { useDetectarErrores } from '../hooks/useDetectarErrores';

interface ErrorDetectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: any[];
  relations: any[];
  onApplyCorrections: (fixedNodes: any[], fixedRelations: any[]) => void;
  xmlContent?: string;
}

export const ErrorDetectionModal: React.FC<ErrorDetectionModalProps> = ({
  isOpen,
  onClose,
  nodes,
  relations,
  onApplyCorrections,
  xmlContent
}) => {
  const {
    loading,
    repairing,
    errorReport,
    selectedError,
    setSelectedError,
    errorMessage,
    ejecutarAnalisis,
    ejecutarReparacion
  } = useDetectarErrores({ nodes, relations, onApplyCorrections });

  useEffect(() => {
    if (isOpen) {
      ejecutarAnalisis(xmlContent);
    }
  }, [isOpen, ejecutarAnalisis, xmlContent]);

  if (!isOpen) return null;

  const renderSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'alta':
        return (
          <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-900/60 text-red-200 border border-red-700/50 flex items-center gap-1">
            <svg className="w-3 h-3 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Alta
          </span>
        );
      case 'media':
        return (
          <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-900/60 text-amber-200 border border-amber-700/50 flex items-center gap-1">
            <svg className="w-3 h-3 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Media
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-900/60 text-blue-200 border border-blue-700/50 flex items-center gap-1">
            <svg className="w-3 h-3 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Baja
          </span>
        );
    }
  };

  const renderTipoBadge = (tipo: string) => {
    const labels: Record<string, string> = {
      sin_pk: 'Sin Clave Primaria (PK)',
      fk_huerfana: 'FK Huérfana',
      tipo_discordante: 'Tipo Discordante',
      dependencia_circular: 'Dependencia Circular',
      relacion_nm_directa: 'Relación N:M Directa',
      tabla_aislada: 'Tabla Aislada',
      palabra_reservada: 'Palabra Reservada SQL'
    };
    return (
      <span className="px-2 py-0.5 text-[11px] font-mono rounded bg-slate-800 text-slate-300 border border-slate-700">
        {labels[tipo] || tipo}
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col text-slate-200 overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">
                Diagnóstico de Errores Lógicos en BD
              </h2>
              <p className="text-xs text-slate-400">
                Auditoría relacional sobre esquema importado (Enterprise Architect XML / Lienzo)
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

        {/* Content Body */}
        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400 gap-3">
              <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-sm font-medium">Analizando esquema de base de datos...</p>
            </div>
          ) : errorMessage ? (
            <div className="flex-1 p-8 flex flex-col items-center justify-center text-red-400 gap-2">
              <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">{errorMessage}</p>
              <button
                onClick={() => ejecutarAnalisis(xmlContent)}
                className="mt-3 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded-md text-white"
              >
                Reintentar
              </button>
            </div>
          ) : !errorReport || errorReport.total_errores === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-white">Esquema Relacionalmente Consistente</h3>
              <p className="text-xs text-slate-400 max-w-md mt-1">
                No se detectaron claves foráneas huérfanas, tablas sin PK, ciclos directos ni relaciones N:M sin resolver. El modelo es apto para despliegue y migraciones SQL.
              </p>
            </div>
          ) : (
            <>
              {/* Lista Izquierda de Errores */}
              <div className="w-full md:w-5/12 border-r border-slate-800/80 overflow-y-auto p-4 space-y-2 bg-slate-950/20">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs font-medium text-slate-400">
                  <span>Inconsistencias ({errorReport.total_errores})</span>
                  <div className="flex gap-2">
                    <span className="text-red-400">{errorReport.estadisticas.sin_pk || 0} sin PK</span>
                    <span>•</span>
                    <span className="text-amber-400">{errorReport.estadisticas.fk_huerfana || 0} FK</span>
                  </div>
                </div>

                {errorReport.errores.map((err) => {
                  const isSelected = selectedError?.id === err.id;
                  return (
                    <div
                      key={err.id}
                      onClick={() => setSelectedError(err)}
                      className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-blue-600/15 border-blue-500/50 shadow-md'
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-xs font-bold text-white tracking-wide">
                          {err.tabla}
                        </span>
                        {renderSeverityBadge(err.severidad)}
                      </div>

                      <div className="mb-2">
                        {renderTipoBadge(err.tipo)}
                      </div>

                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {err.descripcion}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Panel Derecho de Detalle y Acción */}
              <div className="flex-1 flex flex-col p-6 overflow-y-auto">
                {selectedError ? (
                  <div className="space-y-5">
                    <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-base font-bold text-white">
                            Tabla: {selectedError.tabla}
                          </h3>
                          {renderSeverityBadge(selectedError.severidad)}
                        </div>
                        <p className="text-xs text-slate-400 font-mono">
                          ID: {selectedError.id}
                          {selectedError.columna && ` | Atributo: ${selectedError.columna}`}
                        </p>
                      </div>

                      <div>{renderTipoBadge(selectedError.tipo)}</div>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Descripción de la Inconsistencia
                      </h4>
                      <p className="text-sm text-slate-300 bg-slate-950/40 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                        {selectedError.descripcion}
                      </p>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Solución Lógica Aplicable
                      </h4>
                      <div className="text-sm text-emerald-300 bg-emerald-950/20 p-3 rounded-lg border border-emerald-800/40 leading-relaxed flex items-start gap-2">
                        <svg className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span>{selectedError.solucion_sugerida}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
                    Seleccione un error para ver el detalle técnico
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            {errorReport && errorReport.total_errores > 0 && (
              <span>Se aplicarán arreglos automáticos a las {errorReport.total_errores} inconsistencias</span>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cerrar
            </button>

            {errorReport && errorReport.total_errores > 0 && (
              <button
                disabled={repairing}
                onClick={() => ejecutarReparacion(undefined, xmlContent)}
                className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg shadow-lg shadow-blue-600/20 flex items-center gap-2 transition-all"
              >
                {repairing ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Reparando Esquema...
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Reparar Lógica Automáticamente
                  </>
                )}
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
