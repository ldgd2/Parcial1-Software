import React, { useState } from 'react';
import type { ComentarioElemento } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  elementName: string;
  elementoId: string;
  elementoTipo: 'node' | 'relation';
  comentarios: ComentarioElemento[];
  onAgregar: (texto: string) => Promise<any>;
  onCambiarEstado: (id: string, nuevoEstado: 'abierto' | 'resuelto') => Promise<any>;
  onEliminar: (id: string) => Promise<any>;
}

export const CommentThreadModal: React.FC<Props> = ({
  isOpen,
  onClose,
  elementName,
  comentarios,
  onAgregar,
  onCambiarEstado,
  onEliminar
}) => {
  const [nuevoTexto, setNuevoTexto] = useState('');
  const [enviando, setEnviando] = useState(false);

  if (!isOpen) return null;

  const handleEnviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoTexto.trim() || enviando) return;
    setEnviando(true);
    try {
      await onAgregar(nuevoTexto.trim());
      setNuevoTexto('');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(3px)',
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
          maxWidth: '520px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#090d16'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <div>
              <h3 style={{ margin: 0, fontSize: '14px', color: '#f8fafc', fontWeight: 600 }}>
                Comentarios en: {elementName}
              </h3>
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                Hilo de revisión técnica y feedback del elemento
              </span>
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
              padding: '4px'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Lista de comentarios */}
        <div style={{ padding: '16px 18px', overflowY: 'auto', flex: 1, maxHeight: '380px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {comentarios.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 0', color: '#64748b', fontSize: '12px' }}>
              No hay comentarios aún. Deja una nota técnica o feedback abajo.
            </div>
          ) : (
            comentarios.map(c => (
              <div
                key={c.id}
                style={{
                  backgroundColor: '#1e293b',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  borderLeft: `3px solid ${c.estado === 'abierto' ? '#f59e0b' : '#22c55e'}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: '#f8fafc' }}>{c.autor_nombre}</span>
                    <span
                      style={{
                        fontSize: '9px',
                        padding: '1px 5px',
                        borderRadius: '4px',
                        fontWeight: 600,
                        backgroundColor: c.estado === 'abierto' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                        color: c.estado === 'abierto' ? '#f59e0b' : '#22c55e'
                      }}
                    >
                      {c.estado}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => onCambiarEstado(c.id, c.estado === 'abierto' ? 'resuelto' : 'abierto')}
                      style={{
                        background: 'transparent',
                        border: '1px solid #475569',
                        color: '#94a3b8',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        cursor: 'pointer'
                      }}
                    >
                      {c.estado === 'abierto' ? 'Resolver' : 'Reabrir'}
                    </button>
                    <button
                      type="button"
                      onClick={() => onEliminar(c.id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer',
                        padding: '2px'
                      }}
                      title="Eliminar comentario"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                </div>
                <div style={{ fontSize: '12px', color: '#cbd5e1', whiteSpace: 'pre-wrap' }}>
                  {c.texto}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input formulario */}
        <form onSubmit={handleEnviar} style={{ padding: '12px 18px', borderTop: '1px solid #1e293b', backgroundColor: '#090d16', display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={nuevoTexto}
            onChange={e => setNuevoTexto(e.target.value)}
            placeholder="Escribir comentario o nota técnica..."
            style={{
              flex: 1,
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '6px',
              padding: '8px 12px',
              color: '#f8fafc',
              fontSize: '12px',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={enviando || !nuevoTexto.trim()}
            style={{
              backgroundColor: '#38bdf8',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 14px',
              color: '#0f172a',
              fontSize: '12px',
              fontWeight: 600,
              cursor: enviando || !nuevoTexto.trim() ? 'not-allowed' : 'pointer'
            }}
          >
            {enviando ? 'Enviando...' : 'Comentar'}
          </button>
        </form>
      </div>
    </div>
  );
};

