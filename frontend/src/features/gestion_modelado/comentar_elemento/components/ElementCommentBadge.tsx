import React from 'react';

interface Props {
  count: number;
  hasOpen?: boolean;
  onClick: (e: React.MouseEvent) => void;
}

export const ElementCommentBadge: React.FC<Props> = ({ count, hasOpen = false, onClick }) => {
  return (
    <button
      type="button"
      onClick={e => {
        e.stopPropagation();
        onClick(e);
      }}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '3px',
        backgroundColor: hasOpen ? '#b45309' : '#1e293b',
        border: `1px solid ${hasOpen ? '#f59e0b' : '#334155'}`,
        color: '#f8fafc',
        borderRadius: '9999px',
        padding: '2px 6px',
        fontSize: '10px',
        fontWeight: 600,
        cursor: 'pointer',
        userSelect: 'none',
        lineHeight: 1
      }}
      title={`${count} comentarios técnicos en este elemento`}
    >
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
      {count > 0 && <span>{count}</span>}
    </button>
  );
};

