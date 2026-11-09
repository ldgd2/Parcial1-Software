import React, { useState, useRef, useEffect } from 'react';
import type { QuotedMessage, RoomUserMention } from '../../types/chatTypes';
import { QuotedPreview } from './QuotedPreview';
import { MentionList } from './MentionList';
import { CommandList, AVAILABLE_COMMANDS, type SlashCommand } from './CommandList';
import { Plus, FileText, Image as ImageIcon } from 'lucide-react';
import { IconSend, IconMic } from './ChatIcons';
import { callTranscribeAudioAPI } from '../../services/aiChatService';

interface ChatInputBarProps {
  onSendMessage: (text: string) => void;
  replyingTo: QuotedMessage | null;
  onCancelReply: () => void;
  mentionableUsers: RoomUserMention[];
  geminiKey?: string;
  onImageSelected?: (file: File) => void;
  /** Requisitos en PDF (CU36). Si no se pasa, no aparece en el menú "+". */
  onAttachPdf?: (file: File) => void;
  /** Texto para precargar en el campo (p. ej. desde los atajos del chat vacío). */
  draft?: { text: string; nonce: number } | null;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  onSendMessage,
  replyingTo,
  onCancelReply,
  mentionableUsers,
  geminiKey,
  onImageSelected,
  onAttachPdf,
  draft
}) => {
  const [text, setText] = useState('');
  const [showAttach, setShowAttach] = useState(false);
  const attachRef = useRef<HTMLDivElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const hasAttachOptions = !!onImageSelected || !!onAttachPdf;

  // Precargar un borrador y dejar el cursor al final
  useEffect(() => {
    if (!draft) return;
    setText(draft.text);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (el) { el.focus(); el.setSelectionRange(draft.text.length, draft.text.length); }
    });
  }, [draft]);

  // Cerrar el menú "+" al hacer clic fuera o con Escape
  useEffect(() => {
    if (!showAttach) return;
    const onDown = (e: MouseEvent) => {
      if (attachRef.current && !attachRef.current.contains(e.target as Node)) setShowAttach(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setShowAttach(false); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [showAttach]);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const [showCommands, setShowCommands] = useState(false);
  const [commandFilter, setCommandFilter] = useState('');
  const [selectedCmdIndex, setSelectedCmdIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  // Ajuste automático de altura de textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setText(val);

    const cursor = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursor);

    // Detectar si el cursor está inmediatamente después de un '@'
    const lastAtMatch = textBeforeCursor.match(/@([a-zA-Z0-9_\-\.]*)$/);
    if (lastAtMatch) {
      setShowMentions(true);
      setMentionFilter(lastAtMatch[1]);
      setShowCommands(false);
      return;
    } else {
      setShowMentions(false);
    }

    // Detectar si el cursor está inmediatamente después de un '/'
    const lastSlashMatch = textBeforeCursor.match(/(?:^|\s)\/([a-zA-Z0-9_\-]*)$/);
    if (lastSlashMatch) {
      setShowCommands(true);
      setCommandFilter(lastSlashMatch[1]);
      setSelectedCmdIndex(0);
    } else {
      setShowCommands(false);
    }
  };

  const handleSelectMention = (mention: RoomUserMention) => {
    if (!textareaRef.current) return;
    const cursor = textareaRef.current.selectionStart;
    const textBeforeCursor = text.slice(0, cursor);
    const textAfterCursor = text.slice(cursor);
    const replacedBefore = textBeforeCursor.replace(/@([a-zA-Z0-9_\-\.]*)$/, `@${mention.name} `);

    setText(replacedBefore + textAfterCursor);
    setShowMentions(false);
    textareaRef.current.focus();
  };

  const handleSelectCommand = (cmd: SlashCommand) => {
    if (!textareaRef.current) return;
    const cursor = textareaRef.current.selectionStart;
    const textBeforeCursor = text.slice(0, cursor);
    const textAfterCursor = text.slice(cursor);

    const hasBotMention = /@diag\b/i.test(textBeforeCursor);
    let replacedBefore = '';

    if (hasBotMention) {
      replacedBefore = textBeforeCursor.replace(/\/[a-zA-Z0-9_\-]*$/, `/${cmd.command} `);
    } else {
      replacedBefore = textBeforeCursor.replace(/(?:^|\s)\/[a-zA-Z0-9_\-]*$/, `@diag /${cmd.command} `);
    }

    setText(replacedBefore + textAfterCursor);
    setShowCommands(false);
    textareaRef.current.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommands) {
      const cleanFilter = commandFilter.replace(/^\//, '').toLowerCase().trim();
      const filtered = AVAILABLE_COMMANDS.filter(cmd =>
        cmd.command.toLowerCase().includes(cleanFilter) ||
        cmd.description.toLowerCase().includes(cleanFilter)
      );

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedCmdIndex(prev => (prev + 1) % (filtered.length || 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedCmdIndex(prev => (prev - 1 + (filtered.length || 1)) % (filtered.length || 1));
        return;
      }
      if ((e.key === 'Enter' || e.key === 'Tab') && !e.shiftKey) {
        if (filtered.length > 0) {
          e.preventDefault();
          const target = filtered[selectedCmdIndex] || filtered[0];
          handleSelectCommand(target);
          return;
        }
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowCommands(false);
        return;
      }
    }

    if (showMentions) {
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowMentions(false);
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSendMessage(trimmed);
    setText('');
    setShowMentions(false);
    setShowCommands(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  // Grabación y transcripción de voz
  const handleToggleVoice = async () => {
    if (isRecording) {
      // Detener y procesar
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        recorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = async () => {
            const base64Audio = (reader.result as string).split(',')[1];
            if (base64Audio) {
              setIsTranscribing(true);
              try {
                const transcribedText = await callTranscribeAudioAPI(base64Audio, 'audio/webm', geminiKey || null);
                if (transcribedText) {
                  setText(prev => (prev ? `${prev} ${transcribedText}` : transcribedText));
                }
              } catch (err) {
                console.error('Error al transcribir voz:', err);
              } finally {
                setIsTranscribing(false);
              }
            }
          };
        };

        recorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error('No se pudo acceder al micrófono:', err);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onImageSelected) {
      onImageSelected(file);
    }
    if (e.target) e.target.value = '';
  };

  return (
    <div className="whatsapp-input-container">
      {/* Banner de mensaje al que se está respondiendo */}
      {replyingTo && (
        <QuotedPreview
          quote={replyingTo}
          isBanner
          onDismiss={onCancelReply}
        />
      )}

      {/* Popover de autocompletado de menciones */}
      {showMentions && (
        <MentionList
          mentions={mentionableUsers}
          onSelect={handleSelectMention}
          filterText={mentionFilter}
        />
      )}

      {/* Popover de autocompletado de comandos slash */}
      {showCommands && (
        <CommandList
          onSelect={handleSelectCommand}
          filterText={commandFilter}
          selectedIndex={selectedCmdIndex}
        />
      )}

      <div className="whatsapp-input-bar">
        {/* Adjuntar: imagen y/o PDF de requisitos (solo opciones disponibles) */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          hidden
        />
        <input
          type="file"
          ref={pdfInputRef}
          accept="application/pdf,.pdf"
          hidden
          onChange={e => {
            const archivo = e.target.files?.[0];
            e.target.value = '';
            if (archivo && onAttachPdf) onAttachPdf(archivo);
          }}
        />
        {hasAttachOptions && (
          <div className="chat-attach" ref={attachRef}>
            <button
              type="button"
              className={`whatsapp-icon-btn${showAttach ? ' is-on' : ''}`}
              onClick={() => setShowAttach(v => !v)}
              title="Adjuntar"
              aria-label="Adjuntar archivo"
              aria-haspopup="menu"
              aria-expanded={showAttach}
            >
              <Plus size={20} />
            </button>
            {showAttach && (
              <div className="chat-attach__menu" role="menu">
                {onAttachPdf && (
                  <button
                    type="button"
                    role="menuitem"
                    className="chat-attach__item"
                    onClick={() => { setShowAttach(false); pdfInputRef.current?.click(); }}
                  >
                    <FileText size={16} />
                    <span>
                      <strong>PDF de requisitos</strong>
                      <small>La IA lo convierte en una propuesta</small>
                    </span>
                  </button>
                )}
                {onImageSelected && (
                  <button
                    type="button"
                    role="menuitem"
                    className="chat-attach__item"
                    onClick={() => { setShowAttach(false); fileInputRef.current?.click(); }}
                  >
                    <ImageIcon size={16} />
                    <span>
                      <strong>Imagen o bosquejo UML</strong>
                      <small>La IA lo digitaliza como propuesta</small>
                    </span>
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Dictar por voz */}
        <button
          type="button"
          className={`whatsapp-icon-btn ${isRecording ? 'whatsapp-icon-btn--recording' : ''}`}
          onClick={handleToggleVoice}
          title={isRecording ? 'Detener grabación de voz' : 'Dictar requerimiento por voz'}
          aria-label={isRecording ? 'Detener grabación de voz' : 'Dictar por voz'}
          disabled={isTranscribing}
        >
          <IconMic size={20} color={isRecording ? 'var(--danger-text)' : 'currentColor'} />
        </button>

        {/* Área de texto */}
        <textarea
          ref={textareaRef}
          className="whatsapp-textarea"
          placeholder={isTranscribing ? 'Transcribiendo audio...' : 'Escribe un mensaje, @diag o / para comandos...'}
          value={text}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isTranscribing}
        />

        {/* Botón enviar */}
        <button
          type="button"
          className="whatsapp-send-btn"
          onClick={handleSubmit}
          disabled={!text.trim() || isTranscribing}
          title="Enviar mensaje (Enter)"
          aria-label="Enviar mensaje"
        >
          <IconSend size={18} />
        </button>
      </div>
    </div>
  );
};

