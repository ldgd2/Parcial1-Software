import React, { useRef, useEffect } from 'react';
import { useWhatsAppChat } from '../../hooks/useWhatsAppChat';
import { ChatBubble } from './ChatBubble';
import { ChatInputBar } from './ChatInputBar';
import { getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { IconClose, IconUsers } from './ChatIcons';
import {
  useContextoPersistente,
  ContextMemoryBadge,
  ContextModal
} from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente';
import './WhatsAppChat.css';

interface WhatsAppChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  codigoAcceso?: string;
  proyectoId?: number;
  proyectoNombre?: string;
}

export const WhatsAppChatPanel: React.FC<WhatsAppChatPanelProps> = ({
  isOpen,
  onClose,
  codigoAcceso,
  proyectoId,
  proyectoNombre = 'Sala de Modelado'
}) => {
  const {
    messages,
    geminiKey,
    replyingTo,
    setReplyingTo,
    sendMessage,
    inFlightTasks,
    getMentionableUsers
  } = useWhatsAppChat({ codigoAcceso, proyectoId });

  const {
    contexto,
    loading: loadingContexto,
    isModalOpen: isContextModalOpen,
    setIsModalOpen: setIsContextModalOpen,
    reiniciarMemoria
  } = useContextoPersistente({ proyectoId });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentIdentity = getUserIdentity();

  // Desplazar automáticamente al fondo cuando lleguen mensajes nuevos
  useEffect(() => {
    if (messagesEndRef.current && isOpen) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, inFlightTasks, isOpen]);

  if (!isOpen) return null;

  const mentionable = getMentionableUsers();
  const onlineCount = mentionable.length > 1 ? mentionable.length - 1 : 1;

  return (
    <div className="whatsapp-chat-panel">
      {/* Header del Chat estilo WhatsApp */}
      <div className="whatsapp-chat-header">
        <div className="whatsapp-chat-header__left">
          <div className="whatsapp-chat-header__avatar">
            <IconUsers size={20} color="#fff" />
          </div>
          <div className="whatsapp-chat-header__info">
            <span className="whatsapp-chat-header__title">
              {proyectoNombre}
            </span>
            <span className="whatsapp-chat-header__subtitle">
              {onlineCount} {onlineCount === 1 ? 'colaborador' : 'colaboradores'} en línea • @diag activo
            </span>
          </div>
        </div>

        <div className="whatsapp-chat-header__actions">
          {/* Badge de Memoria Persistente de la IA */}
          <ContextMemoryBadge
            contexto={contexto}
            loading={loadingContexto}
            onClick={() => setIsContextModalOpen(true)}
          />

          {/* Cerrar panel */}
          <button
            type="button"
            className="whatsapp-header-btn"
            onClick={onClose}
            title="Cerrar chat"
          >
            <IconClose size={20} />
          </button>
        </div>
      </div>

      {/* Lista de Mensajes */}
      <div className="whatsapp-messages-scroll">
        {messages.map(msg => (
          <ChatBubble
            key={msg.id}
            message={msg}
            currentUserId={currentIdentity.id}
            onReply={quote => setReplyingTo(quote)}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Barra de entrada tipo WhatsApp */}
      <ChatInputBar
        onSendMessage={sendMessage}
        replyingTo={replyingTo}
        onCancelReply={() => setReplyingTo(null)}
        mentionableUsers={mentionable}
        geminiKey={geminiKey}
      />

      {/* Modal de Memoria Persistente de la IA */}
      <ContextModal
        isOpen={isContextModalOpen}
        onClose={() => setIsContextModalOpen(false)}
        contexto={contexto}
        onReiniciar={reiniciarMemoria}
      />
    </div>
  );
};

