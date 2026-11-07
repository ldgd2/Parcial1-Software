import React, { useState, useRef, useEffect } from 'react';
import type { QuotedMessage, RoomUserMention } from '../../types/chatTypes';
import { QuotedPreview } from './QuotedPreview';
import { MentionList } from './MentionList';
import { CommandList, AVAILABLE_COMMANDS, type SlashCommand } from './CommandList';
import { IconSend, IconMic, IconImage } from './ChatIcons';
import { callTranscribeAudioAPI } from '../../services/aiChatService';

interface ChatInputBarProps {
  onSendMessage: (text: string) => void;
  replyingTo: QuotedMessage | null;
  onCancelReply: () => void;
  mentionableUsers: RoomUserMention[];
  geminiKey?: string;
  onImageSelected?: (file: File) => void;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  onSendMessage,
  replyingTo,
  onCancelReply,
  mentionableUsers,
  geminiKey,
  onImageSelected
}) => {
  const [text, setText] = useState('');
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
        {/* Adjuntar imagen */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          style={{ display: 'none' }}
        />
        <button
          type="button"
          className="whatsapp-icon-btn"
          onClick={() => fileInputRef.current?.click()}
          title="Adjuntar imagen o bosquejo UML"
        >
          <IconImage size={20} />
        </button>

        {/* Dictar por voz */}
        <button
          type="button"
          className={`whatsapp-icon-btn ${isRecording ? 'whatsapp-icon-btn--recording' : ''}`}
          onClick={handleToggleVoice}
          title={isRecording ? 'Detener grabación de voz' : 'Dictar requerimiento por voz'}
          disabled={isTranscribing}
        >
          <IconMic size={20} color={isRecording ? '#FF5252' : 'currentColor'} />
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
        >
          <IconSend size={18} color="#fff" />
        </button>
      </div>
    </div>
  );
};

