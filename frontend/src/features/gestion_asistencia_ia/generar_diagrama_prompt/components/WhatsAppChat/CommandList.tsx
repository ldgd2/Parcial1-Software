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
    description: 'Proponer roles de arquitectura y clases por colaborador (se aplican al aprobar)',
    example: '@diag /roles distribuye segun frontend y backend'
  },
  {
    command: 'tareas',
    label: '/tareas',
    description: 'Proponer tareas para el equipo (se crean al aprobar)',
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
  },
  {
    command: 'revisar',
    label: '/revisar',
    description: 'Revisión completa del diagrama con la IA; lo que corrige llega como propuesta',
    example: '@diag /revisar enfócate en las claves foráneas'
  },
  {
    command: 'requisitos',
    label: '/requisitos',
    description: 'Generar el diagrama desde requisitos en texto (o adjuntando un PDF desde el menú +)',
    example: '/requisitos El sistema registra clientes que hacen pedidos de productos…'
  },
  {
    command: 'resumen',
    label: '/resumen',
    description: 'Resumen de lo que cambió: hoy, ayer, semana, N dias o un rango de fechas',
    example: '/resumen ayer'
  },
  {
    command: 'documentar',
    label: '/documentar',
    description: 'Descargar el diccionario de datos del modelo (Markdown)',
    example: '/documentar'
  },
  {
    command: 'ayuda',
    label: '/ayuda',
    description: 'Ver el resumen de comandos y cómo usar el chat',
    example: '/ayuda'
  },
  {
    command: 'sugerencias',
    label: '/sugerencias',
    description: 'Revisar el diagrama ahora y listar lo que se puede mejorar',
    example: '/sugerencias'
  },
  {
    command: 'recordar',
    label: '/recordar',
    description: 'Guardar algo en la memoria del proyecto (la IA lo tendrá en cuenta)',
    example: '/recordar entidades/cliente: el email es único'
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
    case 'ayuda':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      );
    case 'sugerencias':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1V17h6v-.2c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z" />
        </svg>
      );
    case 'recordar':
      return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
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

