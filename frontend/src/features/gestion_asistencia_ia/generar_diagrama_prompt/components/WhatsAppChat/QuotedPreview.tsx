import React from 'react';
import type { QuotedMessage } from '../../types/chatTypes';
import { getUserColor } from '../../utils/chatColors';

interface QuotedPreviewProps {
  quote: QuotedMessage;
  onClick?: () => void;
  isBanner?: boolean; // Si se muestra arriba del input bar
  onDismiss?: () => void;
}

export const QuotedPreview: React.FC<QuotedPreviewProps> = ({
  quote,
  onClick,
  isBanner = false,
  onDismiss
}) => {
  const accentColor = quote.senderColor || getUserColor(quote.senderName);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onClick) {
      onClick();
    } else {
      const targetElement = document.getElementById(`chat-msg-${quote.id}`);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetElement.classList.add('chat-bubble--highlight');
        setTimeout(() => targetElement.classList.remove('chat-bubble--highlight'), 1800);
      }
    }
  };

  return (
    <div
      className={`whatsapp-quote ${isBanner ? 'whatsapp-quote--banner' : ''}`}
      style={{ borderLeftColor: accentColor }}
      onClick={handleClick}
      title="Clic para ir al mensaje original"
    >
      <div className="whatsapp-quote__content">
        <span className="whatsapp-quote__author" style={{ color: accentColor }}>
          {quote.senderName}
        </span>
        <span className="whatsapp-quote__text">
          {quote.text}
        </span>
      </div>
      {isBanner && onDismiss && (
        <button
          type="button"
          className="whatsapp-quote__dismiss"
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }}
          title="Cancelar respuesta"
        >
          ✕
        </button>
      )}
    </div>
  );
};

