import React from 'react';
import type { ContextoIAResponse } from '../types';

interface Props {
  contexto: ContextoIAResponse | null;
  loading?: boolean;
  onClick: () => void;
}

export const ContextMemoryBadge: React.FC<Props> = ({ contexto, loading, onClick }) => {
  const dominio = contexto?.dominio || 'Memoria IA';
  const tokensAhorrados = contexto?.tokens_ahorrados_estimados || 0;
  const eventosCount = contexto?.historial_comprimido?.length || 0;

  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 9px',
        borderRadius: '9999px',
        backgroundColor: 'var(--bg-color)',
        border: '1px solid var(--border-color)',
        color: 'var(--text-muted)',
        fontSize: '11px',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 0.15s ease',
        userSelect: 'none'
      }}
      title={`Memoria persistente activa: ${dominio} (${eventosCount} eventos episódicos, ~${tokensAhorrados} tokens ahorrados)`}
    >
      {/* SVG Brain / Memory Chip Icon */}
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ stroke: 'var(--info)' }} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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

      <span style={{ color: 'var(--text-secondary)', maxWidth: '130px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {loading ? 'Sincronizando...' : dominio}
      </span>

      {tokensAhorrados > 0 && (
        <span style={{ color: 'var(--success-text)', fontSize: '10px', fontWeight: 600 }}>
          +{tokensAhorrados > 1000 ? `${(tokensAhorrados / 1000).toFixed(1)}k` : tokensAhorrados} tok
        </span>
      )}
    </button>
  );
};

