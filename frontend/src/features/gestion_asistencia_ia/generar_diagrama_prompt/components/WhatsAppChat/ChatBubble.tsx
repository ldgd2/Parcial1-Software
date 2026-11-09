import React from 'react';
import type { ChatMessage, QuotedMessage } from '../../types/chatTypes';
import { QuotedPreview } from './QuotedPreview';
import { Square, Download, AlertTriangle, Lightbulb } from 'lucide-react';
import { IconReply, IconDoubleCheck, IconBot } from './ChatIcons';
import { PropuestaCard } from './PropuestaCard';
import { descargarTexto } from '../../utils/comandosIA';

interface ChatBubbleProps {
  message: ChatMessage;
  currentUserId: string;
  onReply: (quote: QuotedMessage) => void;
  /** Propuestas de la IA */
  puedeDecidir?: boolean;
  onDecidirPropuesta?: (messageId: string, aceptar: boolean) => Promise<void>;
  onVerPropuesta?: (versionId: number) => void;
  /** Sugerencias: envía el pedido a @diag (genera una propuesta normal) */
  onAplicarSugerencia?: (pedido: string) => void;
  /** Mientras la IA piensa: detener el pedido (solo quien lo hizo) */
  onDetener?: () => void;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  message,
  currentUserId,
  onReply,
  puedeDecidir = false,
  onDecidirPropuesta,
  onVerPropuesta,
  onAplicarSugerencia,
  onDetener
}) => {
  const isOwn = message.senderId === currentUserId;
  const isAi = message.isAi;

  const formatTime = (ts: number): string => {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatoTokens = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n));

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
      {/* Responder: al costado de la burbuja (no tapa el nombre ni el texto) */}
      <button
        type="button"
        className="whatsapp-bubble__reply-btn"
        onClick={handleReplyClick}
        title="Responder a este mensaje"
        aria-label="Responder a este mensaje"
      >
        <IconReply size={13} />
      </button>
      <div className={`whatsapp-bubble ${isOwn ? 'whatsapp-bubble--own' : 'whatsapp-bubble--other'} ${isAi ? 'whatsapp-bubble--ai' : ''}`}>

        {/* Cita de mensaje respondido */}
        {message.replyTo && (
          <QuotedPreview quote={message.replyTo} />
        )}

        {/* Encabezado del remitente (solo si no es mensaje propio) */}
        {!isOwn && (
          <div className="whatsapp-bubble__header">
            {isAi && <IconBot size={14} color="var(--chat-accent)" />}
            <span className="whatsapp-bubble__sender" style={{ color: message.senderColor }}>
              {message.senderName}
            </span>
          </div>
        )}

        {/* Contenido del mensaje */}
        <div className="whatsapp-bubble__text">
          {message.aiStatus === 'pending' ? (
            <div className="whatsapp-typing-row">
              <div className="whatsapp-typing-wave">
                <span className="whatsapp-typing-dot" />
                <span className="whatsapp-typing-dot" />
                <span className="whatsapp-typing-dot" />
                <span className="whatsapp-typing-dot" />
              </div>
              {onDetener && (
                <button type="button" className="ia-detener__btn" onClick={onDetener} title="Detener a la IA: no se aplica ningún cambio">
                  <Square size={11} fill="currentColor" aria-hidden="true" /> Detener
                </button>
              )}
            </div>
          ) : (
            <>
              {isAi && message.aiStatus === 'error' && (
                <AlertTriangle size={14} className="whatsapp-bubble__estado whatsapp-bubble__estado--error" aria-label="Error" />
              )}
              {isAi && message.aiStatus === 'cancelled' && (
                <Square size={12} fill="currentColor" className="whatsapp-bubble__estado" aria-label="Detenido" />
              )}
              {message.sugerencias && message.sugerencias.length > 0 && (
                <Lightbulb size={14} className="whatsapp-bubble__estado whatsapp-bubble__estado--idea" aria-hidden="true" />
              )}
              {renderFormattedText(message.text)}
            </>
          )}
        </div>

        {message.archivo && (
          <button
            type="button"
            className="sugerencias-ia__btn chat-archivo__btn"
            onClick={() => descargarTexto(message.archivo!.nombre, message.archivo!.contenido)}
          >
            <Download size={13} aria-hidden="true" /> Descargar {message.archivo.nombre}
          </button>
        )}

        {message.sugerencias && message.sugerencias.length > 0 && (
          <ul className="sugerencias-ia">
            {message.sugerencias.map(s => (
              <li key={s.clave} className={`sugerencias-ia__item sugerencias-ia__item--${s.severidad}`}>
                <div className="sugerencias-ia__texto">
                  <span>{s.texto}</span>
                  <span className="sugerencias-ia__detalle">{s.detalle}</span>
                </div>
                {onAplicarSugerencia && (
                  <button type="button" className="sugerencias-ia__btn" onClick={() => onAplicarSugerencia(s.pedido)}>
                    Aplicar
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}

        {message.propuesta && message.aiStatus !== 'pending' && (
          <PropuestaCard
            propuesta={message.propuesta}
            puedeDecidir={puedeDecidir}
            onDecidir={onDecidirPropuesta ? aceptar => onDecidirPropuesta(message.id, aceptar) : undefined}
            onVerCambios={onVerPropuesta ? () => onVerPropuesta(message.propuesta!.versionId) : undefined}
          />
        )}

        {/* Pie: hora y confirmación de lectura */}
        <div className="whatsapp-bubble__footer">
          {isAi && message.usoTokens && message.usoTokens.llamadas > 0 && (
            <span
              className={`whatsapp-bubble__tokens${message.usoTokens.llamadas > 1 ? ' is-varias' : ''}`}
              title={
                `Entrada: ${message.usoTokens.entrada} · Salida: ${message.usoTokens.salida}` +
                ` · ${message.usoTokens.llamadas} llamada(s): ${message.usoTokens.proveedores.join(', ')}` +
                (message.usoTokens.estimado ? ' · estimado' : '')
              }
            >
              {message.usoTokens.estimado ? '≈' : ''}{formatoTokens(message.usoTokens.entrada + message.usoTokens.salida)} tokens
              {message.usoTokens.llamadas > 1 ? ` · ${message.usoTokens.llamadas} llamadas` : ''}
            </span>
          )}
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

