import React, { useRef, useEffect, useCallback, useState } from 'react';
import { Lightbulb, HelpCircle, ArrowDown, Sparkles, History } from 'lucide-react';
import { EVENTO_ABRIR_HISTORIAL, tomarPeticionHistorial } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente/utils/abrirHistorial';
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
import { correccionesDelDiagrama } from '../../hooks/useWhatsAppChat';
import {
  sugerenciasAutoActivas,
  setSugerenciasAuto,
  EVENTO_AJUSTE_SUGERENCIAS,
} from '../../hooks/useSugerenciasAutomaticas';
import { AyudaComandos } from './AyudaComandos';
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
    decidirPropuesta,
    enviarRequisitosPdf,
    enviarImagen,
    enviarAudio,
    detenerIA
  } = useWhatsAppChat({ codigoAcceso, proyectoId, proyectoNombre });

  // CU36: requisitos en PDF (se adjuntan desde el menú "+" de la barra de entrada)
  const [avisoPdf, setAvisoPdf] = useState<string | null>(null);
  const handleAttachPdf = useCallback(async (archivo: File) => {
    setAvisoPdf(`Leyendo ${archivo.name}…`);
    const error = await enviarRequisitosPdf(archivo);
    setAvisoPdf(error);
    if (!error) setTimeout(() => setAvisoPdf(null), 100);
  }, [enviarRequisitosPdf]);

  // Borrador para la barra de entrada (atajos del chat vacío)
  const [draft, setDraft] = useState<{ text: string; nonce: number } | null>(null);
  const usarAtajo = (text: string) => setDraft({ text, nonce: Date.now() });

  // Versión a mostrar al abrir el historial desde una propuesta del chat
  const [versionInicial, setVersionInicial] = useState<number | null>(null);

  const [verAyuda, setVerAyuda] = useState(false);

  // CU33: sugerencias automáticas en el chat (por usuario y proyecto)
  const [sugAuto, setSugAuto] = useState(() => (proyectoId ? sugerenciasAutoActivas(proyectoId) : true));
  useEffect(() => {
    const leer = () => setSugAuto(proyectoId ? sugerenciasAutoActivas(proyectoId) : true);
    window.addEventListener(EVENTO_AJUSTE_SUGERENCIAS, leer);
    return () => window.removeEventListener(EVENTO_AJUSTE_SUGERENCIAS, leer);
  }, [proyectoId]);

  const {
    contexto,
    loading: loadingContexto,
    isModalOpen: isContextModalOpen,
    setIsModalOpen: setIsContextModalOpen,
    reiniciarMemoria,
    guardarInteraccion
  } = useContextoPersistente({ proyectoId });

  // Abrir el historial si lo pidieron desde fuera (menú HERRAMIENTAS)
  useEffect(() => {
    const abrir = () => { if (tomarPeticionHistorial()) setIsContextModalOpen(true); };
    abrir();
    window.addEventListener(EVENTO_ABRIR_HISTORIAL, abrir);
    return () => window.removeEventListener(EVENTO_ABRIR_HISTORIAL, abrir);
  }, [setIsContextModalOpen]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const currentIdentity = getUserIdentity();

  // Scroll inteligente: solo se baja solo si ya estabas al final;
  // si estabas leyendo arriba, se avisa con "↓ N nuevos".
  const atBottomRef = useRef(true);
  const prevCountRef = useRef(messages.length);
  const [unseen, setUnseen] = useState(0);

  const diagram = useDiagram();
  const { isReadOnly, onlineUsers } = useRealTimeSync();

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

  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
    atBottomRef.current = true;
    setUnseen(0);
  }, []);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    atBottomRef.current = atBottom;
    if (atBottom) setUnseen(0);
  }, []);

  // Al abrir el chat, ir al último mensaje
  useEffect(() => {
    if (isOpen) scrollToBottom(false);
  }, [isOpen, scrollToBottom]);

  useEffect(() => {
    if (!isOpen) return;
    const nuevos = messages.length - prevCountRef.current;
    prevCountRef.current = messages.length;
    const ultimo = messages[messages.length - 1];
    const esPropio = !!ultimo && ultimo.senderId === currentIdentity.id;
    if (atBottomRef.current || esPropio) {
      // Al enviar tú, o si ya estabas abajo: seguir el hilo
      scrollToBottom();
    } else if (nuevos > 0) {
      setUnseen(u => u + nuevos);
    }
  }, [messages, inFlightTasks, isOpen, currentIdentity.id, scrollToBottom]);

  if (!isOpen) return null;

  const mentionable = getMentionableUsers();
  // Personas conectadas según el servidor (web + app móvil); alguien en dos dispositivos cuenta una vez
  const conectados = new Set((onlineUsers || []).map((u) => (u.nickname || u.id).trim().toLowerCase()));
  const onlineCount = conectados.size > 0 ? conectados.size : (mentionable.length > 1 ? mentionable.length - 1 : 1);

  return (
    <div className="whatsapp-chat-panel">
      {/* Fila 1: identidad de la sala + cerrar */}
      <div className="whatsapp-chat-header">
        <div className="whatsapp-chat-header__left">
          <div className="whatsapp-chat-header__avatar" aria-hidden="true">
            <IconUsers size={18} />
          </div>
          <div className="whatsapp-chat-header__info">
            <span className="whatsapp-chat-header__title" title={proyectoNombre}>
              {proyectoNombre}
            </span>
            <span className="whatsapp-chat-header__subtitle">
              <span className="whatsapp-chat-header__online" aria-hidden="true" />
              {onlineCount} {onlineCount === 1 ? 'colaborador' : 'colaboradores'} en línea
            </span>
          </div>
        </div>

        <button
          type="button"
          className="whatsapp-header-btn"
          onClick={onClose}
          title="Cerrar chat"
          aria-label="Cerrar chat"
        >
          <IconClose size={20} />
        </button>
      </div>

      {/* Fila 2: herramientas de la IA */}
      <div className="chat-toolbar">
        <div className="chat-toolbar__memoria">
          <ContextMemoryBadge
            contexto={contexto}
            loading={loadingContexto}
            onClick={() => setIsContextModalOpen(true)}
          />
        </div>
        {proyectoId ? (
          <button
            type="button"
            className={`chat-toolbar__btn${sugAuto ? ' is-on' : ''}`}
            onClick={() => setSugerenciasAuto(proyectoId, !sugAuto)}
            title={sugAuto ? 'Sugerencias automáticas activadas: la IA avisa mejoras mientras diagramas' : 'Sugerencias automáticas desactivadas'}
            aria-pressed={sugAuto}
          >
            <Lightbulb size={14} aria-hidden="true" />
            <span>{sugAuto ? 'Auto' : 'Off'}</span>
          </button>
        ) : null}
        <button
          type="button"
          className="chat-toolbar__btn"
          onClick={() => setIsContextModalOpen(true)}
          title="Historial del proyecto: cambios manuales y de la IA, versiones y memoria"
        >
          <History size={14} aria-hidden="true" />
          <span>Historial</span>
        </button>
        <button
          type="button"
          className={`chat-toolbar__btn chat-toolbar__btn--icon${verAyuda ? ' is-on' : ''}`}
          onClick={() => setVerAyuda(v => !v)}
          title="Cómo usar el chat"
          aria-label="Cómo usar el chat"
          aria-pressed={verAyuda}
        >
          <HelpCircle size={15} aria-hidden="true" />
        </button>
      </div>

      {avisoPdf && (
        <div className="chat-aviso" role="status">
          {avisoPdf}
          <button type="button" onClick={() => setAvisoPdf(null)} aria-label="Cerrar">
            <IconClose size={14} />
          </button>
        </div>
      )}

      {/* Lista de mensajes (la ayuda se superpone, no empuja el hilo) */}
      <div className="chat-thread">
      {verAyuda && <AyudaComandos onCerrar={() => setVerAyuda(false)} />}
      <div className="whatsapp-messages-scroll" ref={scrollRef} onScroll={handleScroll}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty__icon" aria-hidden="true"><Sparkles size={22} /></div>
            <p className="chat-empty__title">Chat de la sala con @diag</p>
            <p className="chat-empty__text">
              Pide cambios a la IA con <code>@diag</code> o usa <code>/</code> para comandos.
              Todo llega como propuesta y nadie la aplica sin aprobar.
            </p>
            <div className="chat-empty__chips">
              <button type="button" className="chat-empty__chip" onClick={() => usarAtajo('@diag crea un diagrama de clases para ')}>
                @diag crea un diagrama…
              </button>
              <button type="button" className="chat-empty__chip" onClick={() => usarAtajo('@diag /revisar')}>
                /revisar
              </button>
              <button type="button" className="chat-empty__chip" onClick={() => usarAtajo('@diag /roles')}>
                /roles
              </button>
              <button type="button" className="chat-empty__chip" onClick={() => usarAtajo('@diag /tareas')}>
                /tareas
              </button>
            </div>
          </div>
        )}
        {messages.map(msg => (
          <ChatBubble
            key={msg.id}
            message={msg}
            currentUserId={currentIdentity.id}
            onReply={quote => setReplyingTo(quote)}
            puedeDecidir={!isReadOnly}
            onDecidirPropuesta={decidirPropuesta}
            onAplicarSugerencia={pedido => sendMessage(`@diag ${pedido}`)}
            onDetener={
              msg.isAi && msg.aiStatus === 'pending' && msg.replyTo &&
              inFlightTasks.some(t => t.promptMessageId === msg.replyTo!.id)
                ? () => detenerIA(msg.replyTo!.id)
                : undefined
            }
            onVerPropuesta={versionId => {
              setVersionInicial(versionId);
              setIsContextModalOpen(true);
            }}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
      {unseen > 0 && (
        <button type="button" className="chat-nuevos" onClick={() => scrollToBottom()}>
          <ArrowDown size={14} aria-hidden="true" />
          {unseen} {unseen === 1 ? 'nuevo' : 'nuevos'}
        </button>
      )}
      </div>

      {/* Barra de entrada */}
      <ChatInputBar
        onSendMessage={sendMessage}
        replyingTo={replyingTo}
        onCancelReply={() => setReplyingTo(null)}
        mentionableUsers={mentionable}
        geminiKey={geminiKey}
        onAttachPdf={proyectoId ? handleAttachPdf : undefined}
        onSendImage={enviarImagen}
        onSendAudio={enviarAudio}
        draft={draft}
      />

      {/* Modal de Memoria Persistente de la IA */}
      <ContextModal
        isOpen={isContextModalOpen}
        onClose={() => {
          setIsContextModalOpen(false);
          setVersionInicial(null);
        }}
        versionInicial={versionInicial}
        correccionesDiagrama={correccionesDelDiagrama(diagram.getDiagramState(), diagram.nodes)}
        contexto={contexto}
        onReiniciar={reiniciarMemoria}
        proyectoId={proyectoId}
        puedeRestaurar={!isReadOnly}
        onRestaurar={handleRestaurarVersion}
      />
    </div>
  );
};

