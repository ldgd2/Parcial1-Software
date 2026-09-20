import React, { useState } from 'react';
import './UrlCopyCard.css';

export interface UrlCopyCardProps {
  label: string;
  url: string;
  icon?: React.ReactNode;
  badgeText?: string;
  highlight?: boolean;
}

export const UrlCopyCard: React.FC<UrlCopyCardProps> = ({
  label,
  url,
  icon,
  badgeText,
  highlight = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSelectText = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.select();
  };

  return (
    <div className={`url-copy-card ${highlight ? 'highlight' : ''}`}>
      <div className="url-copy-card-header">
        <div className="url-copy-card-title">
          {icon || (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
          )}
          <strong>{label}</strong>
        </div>
        {badgeText && <span className="url-copy-card-badge">{badgeText}</span>}
      </div>

      <div className="url-copy-card-input-row">
        <input
          type="text"
          className="url-copy-card-input"
          value={url}
          readOnly
          onFocus={handleSelectText}
          onClick={(e) => (e.target as HTMLInputElement).select()}
        />
        <div className="url-copy-card-actions">
          <button
            type="button"
            className={`url-copy-action-btn copy-btn ${copied ? 'copied' : ''}`}
            onClick={handleCopy}
            title="Copiar URL al portapapeles"
          >
            {copied ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>¡Copiado!</span>
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>Copiar</span>
              </>
            )}
          </button>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="url-copy-action-btn open-btn"
            title="Abrir en ventana nueva"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="7" y1="17" x2="17" y2="7" />
              <polyline points="7 7 17 7 17 17" />
            </svg>
            <span>Abrir</span>
          </a>
        </div>
      </div>
    </div>
  );
};
