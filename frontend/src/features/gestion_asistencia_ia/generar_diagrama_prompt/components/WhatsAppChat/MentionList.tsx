import React from 'react';
import type { RoomUserMention } from '../../types/chatTypes';
import { IconBot } from './ChatIcons';

interface MentionListProps {
  mentions: RoomUserMention[];
  onSelect: (mention: RoomUserMention) => void;
  filterText: string;
}

export const MentionList: React.FC<MentionListProps> = ({
  mentions,
  onSelect,
  filterText
}) => {
  const filtered = mentions.filter(m =>
    m.name.toLowerCase().includes(filterText.toLowerCase())
  );

  if (filtered.length === 0) return null;

  return (
    <div className="whatsapp-mention-popup">
      <div className="whatsapp-mention-popup__title">
        Mencionar participante o IA
      </div>
      <div className="whatsapp-mention-popup__list">
        {filtered.map(item => (
          <button
            key={item.id}
            type="button"
            className="whatsapp-mention-item"
            onClick={() => onSelect(item)}
          >
            <div
              className="whatsapp-mention-item__avatar"
              style={{ backgroundColor: item.color }}
            >
              {item.isAi ? <IconBot size={13} color="#fff" /> : item.name.charAt(0).toUpperCase()}
            </div>
            <div className="whatsapp-mention-item__info">
              <span className="whatsapp-mention-item__name">
                @{item.name}
              </span>
              {item.isAi ? (
                <span className="whatsapp-mention-item__desc">
                  Asistente IA (Diagramas y Tareas)
                </span>
              ) : (
                <span className="whatsapp-mention-item__desc">
                  Colaborador de la sala
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

