import React from 'react';

export interface SlashCommand {
  command: string;
  label: string;
  description: string;
  example: string;
}

export const AVAILABLE_COMMANDS: SlashCommand[] = [
  {
    command: 'roles',
    label: '/roles',
    description: 'Repartir roles de arquitectura y asignar clases a colaboradores',
    example: '@diag /roles distribuye segun frontend y backend'
  },
  {
    command: 'tareas',
    label: '/tareas',
    description: 'Generar backlog de tareas y registrarlas en el proyecto',
    example: '@diag /tareas crea tareas para modelar y programar'
  },
  {
    command: 'optimizar',
    label: '/optimizar',
    description: 'Optimizar relaciones, cardinalidades y normalizar atributos',
    example: '@diag /optimizar revisa coherencia del diagrama'
  },
  {
    command: 'explicar',
    label: '/explicar',
    description: 'Explicar arquitectura, patrones y flujo del diagrama',
    example: '@diag /explicar como funciona el modulo de usuarios'
  },
  {
    command: 'limpiar',
    label: '/limpiar',
    description: 'Limpiar elementos no conectados o notas obsoletas',
    example: '@diag /limpiar quita clases no utilizadas'
  }
];

const renderCommandIcon = (command: string) => {
  switch (command) {
    case 'roles':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      );
    case 'tareas':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="9 11 12 14 22 4" />
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
        </svg>
      );
    case 'optimizar':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
      );
    case 'explicar':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      );
    case 'limpiar':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
      );
    default:
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="4 17 10 11 4 5" />
          <line x1="12" y1="19" x2="20" y2="19" />
        </svg>
      );
  }
};

interface CommandListProps {
  onSelect: (command: SlashCommand) => void;
  filterText: string;
  selectedIndex?: number;
}

export const CommandList: React.FC<CommandListProps> = ({
  onSelect,
  filterText,
  selectedIndex = 0
}) => {
  const cleanFilter = filterText.replace(/^\//, '').toLowerCase().trim();
  const filtered = AVAILABLE_COMMANDS.filter(cmd =>
    cmd.command.toLowerCase().includes(cleanFilter) ||
    cmd.description.toLowerCase().includes(cleanFilter)
  );

  if (filtered.length === 0) return null;

  return (
    <div className="whatsapp-mention-popup whatsapp-command-popup">
      <div className="whatsapp-mention-popup__title">
        Comandos de Asistente IA (@diag)
      </div>
      <div className="whatsapp-mention-popup__list">
        {filtered.map((cmd, index) => {
          const isSelected = index === selectedIndex;
          return (
            <button
              key={cmd.command}
              type="button"
              className={`whatsapp-mention-item whatsapp-command-item ${isSelected ? 'whatsapp-command-item--selected' : ''}`}
              onClick={() => onSelect(cmd)}
            >
              <div className="whatsapp-command-item__icon">
                {renderCommandIcon(cmd.command)}
              </div>
              <div className="whatsapp-mention-item__info" style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="whatsapp-command-item__label">
                    {cmd.label}
                  </span>
                  <span className="whatsapp-command-item__example">
                    {cmd.example}
                  </span>
                </div>
                <span className="whatsapp-mention-item__desc">
                  {cmd.description}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

