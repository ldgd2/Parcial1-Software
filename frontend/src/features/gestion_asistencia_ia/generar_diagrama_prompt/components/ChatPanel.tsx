import React from 'react';
import { WhatsAppChatPanel } from './WhatsAppChat/WhatsAppChatPanel';
import { useParams, useSearchParams } from 'react-router-dom';
import './ChatPanel.css';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  codigoAcceso?: string;
  proyectoId?: number;
  proyectoNombre?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  isOpen,
  onClose,
  codigoAcceso: propCodigo,
  proyectoId: propProyectoId,
  proyectoNombre = 'Sala de Modelado'
}) => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const queryCodigo = searchParams.get('codigo') || undefined;

  if (!isOpen) return null;

  const codigo = propCodigo || queryCodigo || (id ? `proj_${id}` : 'sala_global');
  const numericProyectoId = propProyectoId || (id ? parseInt(id, 10) : undefined);

  return (
    <div className="chat-panel" style={{ width: '380px', padding: 0 }}>
      <WhatsAppChatPanel
        isOpen={isOpen}
        onClose={onClose}
        codigoAcceso={codigo}
        proyectoId={numericProyectoId}
        proyectoNombre={proyectoNombre}
      />
    </div>
  );
};
