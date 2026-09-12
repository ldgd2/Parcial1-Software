import React from 'react';
import { useSalaSocket } from '../../context/SalaSocketContext';
import './MultiplayerCursors.css';

export const MultiplayerCursors: React.FC = () => {
  const { cursors } = useSalaSocket();

  return (
    <div className="multiplayer-cursors" style={{ pointerEvents: 'none', position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }}>
      {Object.entries(cursors).map(([id, cursor]) => (
        <div
          key={id}
          className="multiplayer-cursor"
          style={{
            position: 'absolute',
            left: cursor.x,
            top: cursor.y,
            transform: 'translate(-50%, -50%)',
            transition: 'left 0.05s linear, top 0.05s linear'
          }}
        >
          {/* Custom Mouse Cursor SVG */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4.5 4.5L11.5 20.5L14 14L20.5 11.5L4.5 4.5Z" fill="#FF5722" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
          </svg>
          <div className="multiplayer-cursor__name" style={{
            background: '#FF5722',
            color: 'white',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            position: 'absolute',
            top: '20px',
            left: '10px',
            whiteSpace: 'nowrap',
            fontWeight: 'bold',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}>
            {cursor.nickname}
          </div>
        </div>
      ))}
    </div>
  );
};
