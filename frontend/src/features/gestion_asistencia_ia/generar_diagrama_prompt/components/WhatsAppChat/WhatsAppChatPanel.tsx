import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useWhatsAppChat } from '../../hooks/useWhatsAppChat';
import { ChatBubble } from './ChatBubble';
import { ChatInputBar } from './ChatInputBar';
import { getUserIdentity, useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { IconClose, IconUsers } from './ChatIcons';
import {
  useContextoPersistente,
  ContextMemoryBadge,
  ContextModal,
  compararVersiones,
  restaurarVersion,
  EVENTO_VERSIONES_ACTUALIZADAS,
  pausarRegistroManual,
  type EstadoDiagramaVersion,
  type VersionResumen
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
    getMentionableUsers,
    decidirPropuesta
  } = useWhatsAppChat({ codigoAcceso, proyectoId });

  // Versión a mostrar al abrir el historial desde una propuesta del chat
  const [versionInicial, setVersionInicial] = useState<number | null>(null);

  const {
    contexto,
    loading: loadingContexto,
    isModalOpen: isContextModalOpen,
    setIsModalOpen: setIsContextModalOpen,
    reiniciarMemoria,
    guardarInteraccion
  } = useContextoPersistente({ proyectoId });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentIdentity = getUserIdentity();

  const diagram = useDiagram();
  const { isReadOnly } = useRealTimeSync();

  // Restaurar una versión del historial en la pizarra de toda la sala
  const handleRestaurarVersion = useCallback(async (
    objetivo: EstadoDiagramaVersion,
    version: VersionResumen,
    lado: 'antes' | 'despues'
  ) => {
    const { nodes, relations } = diagram.getDiagramState();
    const actual: EstadoDiagramaVersion = { nodes, relations };
    const cambios = compararVersiones(actual, objetivo);

    pausarRegistroManual(3000);   // la restauración se registra como su propia versión
    restaurarVersion(actual, objetivo, diagram);

    // Queda registrada como una interacción nueva (no se reescribe el historial)
    await guardarInteraccion({
      user_prompt: `Restaurar la versión ${lado === 'antes' ? 'anterior' : 'posterior'} a «${version.cmd}»`,
      intent: 'RESTAURAR',
      added_nodes: cambios.nodos.filter(n => n.estado === 'agregado').map(n => n.nombre),
      updated_nodes: cambios.nodos.filter(n => n.estado === 'modificado').map(n => n.nombre),
      deleted_nodes: cambios.nodos.filter(n => n.estado === 'eliminado').map(n => n.nombre),
      estado_antes: actual,
      estado_despues: objetivo,
      autor: currentIdentity.nickname
    });
    window.dispatchEvent(new CustomEvent(EVENTO_VERSIONES_ACTUALIZADAS, { detail: {} }));
  }, [diagram, guardarInteraccion, currentIdentity.nickname]);

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
            puedeDecidir={!isReadOnly}
            onDecidirPropuesta={decidirPropuesta}
            onVerPropuesta={versionId => {
              setVersionInicial(versionId);
              setIsContextModalOpen(true);
            }}
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
        onClose={() => {
          setIsContextModalOpen(false);
          setVersionInicial(null);
        }}
        versionInicial={versionInicial}
        contexto={contexto}
        onReiniciar={reiniciarMemoria}
        proyectoId={proyectoId}
        puedeRestaurar={!isReadOnly}
        onRestaurar={handleRestaurarVersion}
      />
    </div>
  );
};

