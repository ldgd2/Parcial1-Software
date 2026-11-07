import React, { useState } from 'react';
import type { ContextoIAResponse } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  contexto: ContextoIAResponse | null;
  onReiniciar: () => Promise<any>;
}

export const ContextModal: React.FC<Props> = ({ isOpen, onClose, contexto, onReiniciar }) => {
  const [activeTab, setActiveTab] = useState<'historial' | 'correcciones' | 'compilado'>('historial');
  const [copiado, setCopiado] = useState(false);
  const [reiniciando, setReiniciando] = useState(false);

  if (!isOpen) return null;

  const handleCopiarCompilado = () => {
    if (!contexto?.contexto_compilado_llm) return;
    navigator.clipboard.writeText(contexto.contexto_compilado_llm);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  const handleConfirmarReinicio = async () => {
    if (!window.confirm('¿Deseas reiniciar la memoria persistente de la IA para este proyecto? Se restablecerá el historial de interacciones.')) {
      return;
    }
    setReiniciando(true);
    try {
      await onReiniciar();
    } finally {
      setReiniciando(false);
    }
  };

  const eventos = contexto?.historial_comprimido || [];
  const correcciones = contexto?.correcciones || [];
  const tokensAhorrados = contexto?.tokens_ahorrados_estimados || 0;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 99999,
        padding: '16px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '720px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 20px',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#090d16'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <rect x="9" y="9" width="6" height="6" />
              <line x1="9" y1="1" x2="9" y2="4" />
              <line x1="15" y1="1" x2="15" y2="4" />
              <line x1="9" y1="20" x2="9" y2="23" />
              <line x1="15" y1="20" x2="15" y2="23" />
              <line x1="20" y1="9" x2="23" y2="9" />
              <line x1="20" y1="14" x2="23" y2="14" />
              <line x1="1" y1="9" x2="4" y2="9" />
              <line x1="1" y1="14" x2="4" y2="14" />
            </svg>
            <div>
              <h3 style={{ margin: 0, fontSize: '15px', color: '#f8fafc', fontWeight: 600 }}>
                Memoria Persistente de la IA
              </h3>
              <p style={{ margin: 0, fontSize: '11px', color: '#64748b' }}>
                Contexto cognitivo ultra-comprimido para optimización extrema de tokens
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '6px'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Metric Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', padding: '14px 20px', borderBottom: '1px solid #1e293b' }}>
          <div style={{ backgroundColor: '#1e293b', padding: '10px 12px', borderRadius: '8px' }}>
            <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Dominio Inferido</span>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {contexto?.dominio || 'General'}
            </div>
          </div>
          <div style={{ backgroundColor: '#1e293b', padding: '10px 12px', borderRadius: '8px' }}>
            <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Eventos Memorizados</span>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#38bdf8', marginTop: '2px' }}>
              {eventos.length} interacciones
            </div>
          </div>
          <div style={{ backgroundColor: '#1e293b', padding: '10px 12px', borderRadius: '8px' }}>
            <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Tokens Ahorrados</span>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#4ade80', marginTop: '2px' }}>
              ~{tokensAhorrados > 1000 ? `${(tokensAhorrados / 1000).toFixed(1)}k` : tokensAhorrados} tok
            </div>
          </div>
        </div>

        {/* Tab navigation */}
        <div style={{ display: 'flex', gap: '8px', padding: '10px 20px 0 20px', borderBottom: '1px solid #1e293b' }}>
          <button
            type="button"
            onClick={() => setActiveTab('historial')}
            style={{
              padding: '8px 12px',
              backgroundColor: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'historial' ? '2px solid #38bdf8' : '2px solid transparent',
              color: activeTab === 'historial' ? '#f8fafc' : '#64748b',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Historial Episódico ({eventos.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('correcciones')}
            style={{
              padding: '8px 12px',
              backgroundColor: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'correcciones' ? '2px solid #38bdf8' : '2px solid transparent',
              color: activeTab === 'correcciones' ? '#f8fafc' : '#64748b',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Correcciones Activas ({correcciones.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('compilado')}
            style={{
              padding: '8px 12px',
              backgroundColor: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'compilado' ? '2px solid #38bdf8' : '2px solid transparent',
              color: activeTab === 'compilado' ? '#f8fafc' : '#64748b',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Prompt Memory Inyectado
          </button>
        </div>

        {/* Content body */}
        <div style={{ padding: '16px 20px', overflowY: 'auto', flex: 1, maxHeight: '360px' }}>
          {activeTab === 'historial' && (
            <div>
              {eventos.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px 0', color: '#64748b', fontSize: '13px' }}>
                  No hay interacciones registradas aún. El historial se compilará automáticamente en el próximo comando.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {eventos.slice().reverse().map((ev, i) => (
                    <div
                      key={i}
                      style={{
                        backgroundColor: '#1e293b',
                        padding: '10px 12px',
                        borderRadius: '6px',
                        borderLeft: '3px solid #38bdf8'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8' }}>
                          [{ev.intent}] {ev.cmd}
                        </span>
                        <span style={{ fontSize: '10px', color: '#64748b' }}>
                          {new Date(ev.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '4px' }}>
                        {ev.summary}
                      </div>
                      {(() => {
                        const sanitizedDelta = (ev.delta || '')
                          .split('|')
                          .map(part => part.trim())
                          .map(part => {
                            if (part.startsWith('-')) {
                              const filtered = part.slice(1).split(',').filter(x => !/^node_\w+$/i.test(x.trim()) && !['diagrama', 'eliminadas', 'borradas'].includes(x.trim().toLowerCase()));
                              return filtered.length > 0 ? `-${filtered.join(',')}` : '';
                            }
                            return part;
                          })
                          .filter(Boolean)
                          .join(' | ');

                        return sanitizedDelta && sanitizedDelta !== 'sin_cambios' ? (
                          <div style={{ fontSize: '11px', color: '#a78bfa', fontFamily: 'monospace' }}>
                            Delta: {sanitizedDelta}
                          </div>
                        ) : null;
                      })()}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'correcciones' && (
            <div>
              {correcciones.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px 0', color: '#64748b', fontSize: '13px' }}>
                  No hay correcciones o requerimientos pendientes registrados.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {correcciones.map((corr, i) => (
                    <div
                      key={i}
                      style={{
                        backgroundColor: '#1e293b',
                        padding: '10px 12px',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}
                    >
                      <div>
                        <span style={{ fontSize: '11px', fontWeight: 600, color: '#f59e0b', marginRight: '8px' }}>
                          [{corr.target}]
                        </span>
                        <span style={{ fontSize: '12px', color: '#f8fafc' }}>
                          {corr.text}
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 600,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: corr.estado === 'abierta' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                          color: corr.estado === 'abierta' ? '#f87171' : '#4ade80'
                        }}
                      >
                        {corr.estado}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'compilado' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                  Bloque exacto inyectado en cada consulta al LLM:
                </span>
                <button
                  type="button"
                  onClick={handleCopiarCompilado}
                  style={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    color: '#f8fafc',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    cursor: 'pointer'
                  }}
                >
                  {copiado ? 'Copiado' : 'Copiar'}
                </button>
              </div>
              <pre
                style={{
                  backgroundColor: '#090d16',
                  padding: '12px',
                  borderRadius: '6px',
                  color: '#38bdf8',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  margin: 0,
                  border: '1px solid #1e293b'
                }}
              >
                {contexto?.contexto_compilado_llm || 'Sin memoria compilada activa.'}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#090d16'
          }}
        >
          <button
            type="button"
            onClick={handleConfirmarReinicio}
            disabled={reiniciando}
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid #ef4444',
              color: '#f87171',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: reiniciando ? 'not-allowed' : 'pointer'
            }}
          >
            {reiniciando ? 'Reiniciando...' : 'Reiniciar Memoria del Proyecto'}
          </button>

          <button
            type="button"
            onClick={onClose}
            style={{
              backgroundColor: '#38bdf8',
              border: 'none',
              color: '#0f172a',
              padding: '6px 16px',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};

