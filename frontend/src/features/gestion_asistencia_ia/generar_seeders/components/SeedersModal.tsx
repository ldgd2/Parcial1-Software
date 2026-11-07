import React, { useEffect } from 'react';
import { useGenerarSeeders } from '../hooks/useGenerarSeeders';
import type { ClassNode, Relation } from '@/features/gestion_modelado/shared/types/types';

interface SeedersModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: ClassNode[];
  relations: Relation[];
  proyectoId?: number;
}

export const SeedersModal: React.FC<SeedersModalProps> = ({
  isOpen,
  onClose,
  nodes,
  relations,
  proyectoId
}) => {
  const {
    loading,
    cantidad,
    setCantidad,
    formato,
    setFormato,
    resultado,
    errorMessage,
    copied,
    ejecutarGeneracion,
    copiarAlPortapapeles,
    descargarArchivo
  } = useGenerarSeeders({ nodes, relations, proyectoId });

  useEffect(() => {
    if (isOpen) {
      ejecutarGeneracion();
    }
  }, [isOpen, cantidad, formato]);

  if (!isOpen) return null;

  const codigoActual = resultado
    ? (formato === 'sql' ? resultado.sql_script : (resultado.java_code || resultado.sql_script))
    : '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col text-slate-200 overflow-hidden">

        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7zM9 9h6M9 13h6M9 17h4" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">
                Generador de Seeders de Base de Datos
              </h2>
              <p className="text-xs text-slate-400">
                Población de datos coherentes para pruebas con ordenamiento topológico referencial
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

        {/* Controls Toolbar */}
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/20 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Registros por tabla:
            </span>
            <div className="flex bg-slate-800/70 p-0.5 rounded-lg border border-slate-700/60">
              {[5, 10, 20, 50].map(c => (
                <button
                  key={c}
                  onClick={() => setCantidad(c)}
                  className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                    cantidad === c
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Formato:
            </span>
            <div className="flex bg-slate-800/70 p-0.5 rounded-lg border border-slate-700/60">
              <button
                onClick={() => setFormato('sql')}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                  formato === 'sql'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                PostgreSQL (.sql)
              </button>
              <button
                onClick={() => setFormato('java_runner')}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                  formato === 'java_runner'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Spring Boot (Java)
              </button>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400 gap-3">
              <svg className="animate-spin h-8 w-8 text-emerald-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-sm font-medium">Generando dataset coherente...</p>
            </div>
          ) : errorMessage ? (
            <div className="flex-1 p-8 flex flex-col items-center justify-center text-red-400 gap-2">
              <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">{errorMessage}</p>
            </div>
          ) : (
            <>
              {/* Resumen Superior */}
              {resultado && (
                <div className="px-6 py-2.5 bg-slate-950/50 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{resultado.resumen}</span>
                  </div>

                  <div className="flex gap-2">
                    <span className="text-slate-300 font-mono">
                      Orden: {resultado.orden_insercion.slice(0, 4).join(' → ')}
                      {resultado.orden_insercion.length > 4 ? '...' : ''}
                    </span>
                  </div>
                </div>
              )}

              {/* Code Preview Box */}
              <div className="flex-1 overflow-auto bg-slate-950 p-4 font-mono text-xs text-slate-300 leading-relaxed select-text">
                <pre className="whitespace-pre">{codigoActual}</pre>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            {resultado && (
              <span>
                Total: <strong className="text-white">{resultado.total_registros}</strong> registros en{' '}
                <strong className="text-white">{resultado.total_tablas}</strong> tablas
              </span>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={copiarAlPortapapeles}
              disabled={!resultado || loading}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded-lg flex items-center gap-2 transition-colors"
            >
              {copied ? (
                <>
                  <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Copiado</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                  <span>Copiar Script</span>
                </>
              )}
            </button>

            <button
              onClick={descargarArchivo}
              disabled={!resultado || loading}
              className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg shadow-lg shadow-emerald-600/20 flex items-center gap-2 transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Descargar Archivo</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

