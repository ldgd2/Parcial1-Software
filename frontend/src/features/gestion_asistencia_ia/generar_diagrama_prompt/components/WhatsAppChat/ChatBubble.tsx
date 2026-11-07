import React from 'react';
import type { ChatMessage, QuotedMessage } from '../../types/chatTypes';
import { QuotedPreview } from './QuotedPreview';
import { IconReply, IconDoubleCheck, IconBot } from './ChatIcons';

interface ChatBubbleProps {
  message: ChatMessage;
  currentUserId: string;
  onReply: (quote: QuotedMessage) => void;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  message,
  currentUserId,
  onReply
}) => {
  const isOwn = message.senderId === currentUserId;
  const isAi = message.isAi;

  const formatTime = (ts: number): string => {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderFormattedText = (text: string) => {
    // Resaltar menciones (@diag, @nombre) y comandos (/roles, /tareas, etc.)
    const parts = text.split(/(@[a-zA-Z0-9_\-\.]+|\/[a-zA-Z0-9_\-]+)/g);
    return parts.map((part, index) => {
      const lower = part.toLowerCase();
      if (lower === '@diag') {
        return (
          <span key={index} className="whatsapp-mention whatsapp-mention--ai">
            {part}
          </span>
        );
      }
      if (part.startsWith('@')) {
        return (
          <span key={index} className="whatsapp-mention">
            {part}
          </span>
        );
      }
      if (part.startsWith('/')) {
        return (
          <span key={index} className="whatsapp-command-badge">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const handleReplyClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onReply({
      id: message.id,
      senderName: message.senderName,
      text: message.text,
      senderColor: message.senderColor
    });
  };

  return (
    <div
      id={`chat-msg-${message.id}`}
      className={`whatsapp-bubble-wrapper ${isOwn ? 'whatsapp-bubble-wrapper--own' : 'whatsapp-bubble-wrapper--other'}`}
    >
      <div className={`whatsapp-bubble ${isOwn ? 'whatsapp-bubble--own' : 'whatsapp-bubble--other'} ${isAi ? 'whatsapp-bubble--ai' : ''}`}>
        {/* Botón flotante para responder */}
        <button
          type="button"
          className="whatsapp-bubble__reply-btn"
          onClick={handleReplyClick}
          title="Responder a este mensaje"
        >
          <IconReply size={13} />
        </button>

        {/* Cita de mensaje respondido */}
        {message.replyTo && (
          <QuotedPreview quote={message.replyTo} />
        )}

        {/* Encabezado del remitente (solo si no es mensaje propio) */}
        {!isOwn && (
          <div className="whatsapp-bubble__header">
            {isAi && <IconBot size={14} color="#25D366" />}
            <span className="whatsapp-bubble__sender" style={{ color: message.senderColor }}>
              {message.senderName}
            </span>
            {isAi && message.provider && (
              <span className="whatsapp-bubble__provider-tag">
                {message.provider.toUpperCase()}
              </span>
            )}
          </div>
        )}

        {/* Contenido del mensaje */}
        <div className="whatsapp-bubble__text">
          {message.aiStatus === 'pending' ? (
            <div className="whatsapp-bubble__loading">
              <span className="whatsapp-typing-dot" />
              <span className="whatsapp-typing-dot" />
              <span className="whatsapp-typing-dot" />
              <span style={{ marginLeft: 6 }}>{message.text}</span>
            </div>
          ) : (
            renderFormattedText(message.text)
          )}
        </div>

        {/* Pie: hora y confirmación de lectura */}
        <div className="whatsapp-bubble__footer">
          <span className="whatsapp-bubble__time">
            {formatTime(message.timestamp)}
          </span>
          {isOwn && (
            <span className="whatsapp-bubble__checks">
              <IconDoubleCheck size={14} />
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

