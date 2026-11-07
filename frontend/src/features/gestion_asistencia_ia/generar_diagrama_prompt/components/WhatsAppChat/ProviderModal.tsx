import React, { useState } from 'react';
import type { AiProvider } from '../../types/chatTypes';
import { IconClose } from './ChatIcons';

interface ProviderModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeProvider: AiProvider;
  onSelectProvider: (p: AiProvider) => void;
  geminiKey: string;
  onSaveGeminiKey: (k: string) => void;
  openrouterKey: string;
  onSaveOpenrouterKey: (k: string) => void;
  kimiKey: string;
  onSaveKimiKey: (k: string) => void;
}

export const ProviderModal: React.FC<ProviderModalProps> = ({
  isOpen,
  onClose,
  activeProvider,
  onSelectProvider,
  geminiKey,
  onSaveGeminiKey,
  openrouterKey,
  onSaveOpenrouterKey,
  kimiKey,
  onSaveKimiKey
}) => {
  const [localGeminiKey, setLocalGeminiKey] = useState(geminiKey);
  const [localOpenrouterKey, setLocalOpenrouterKey] = useState(openrouterKey);
  const [localKimiKey, setLocalKimiKey] = useState(kimiKey);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveGeminiKey(localGeminiKey.trim());
    onSaveOpenrouterKey(localOpenrouterKey.trim());
    onSaveKimiKey(localKimiKey.trim());
    onClose();
  };

  return (
    <div className="whatsapp-modal-backdrop" onClick={onClose}>
      <div className="whatsapp-modal" onClick={e => e.stopPropagation()}>
        <div className="whatsapp-modal__header">
          <h3>Configuracion de Proveedor de IA</h3>
          <button type="button" className="whatsapp-modal__close" onClick={onClose}>
            <IconClose size={18} />
          </button>
        </div>

        <div className="whatsapp-modal__body">
          <p className="whatsapp-modal__desc">
            Alterna el motor de inteligencia artificial que respondera a las instrucciones con <strong>@diag</strong> en el chat y procesara imagenes o diagramas.
          </p>

          <div className="whatsapp-provider-cards">
            {/* Tarjeta Gemini */}
            <div
              className={`whatsapp-provider-card ${activeProvider === 'gemini' ? 'whatsapp-provider-card--active' : ''}`}
              onClick={() => onSelectProvider('gemini')}
            >
              <div className="whatsapp-provider-card__radio">
                <input
                  type="radio"
                  name="ai_provider"
                  checked={activeProvider === 'gemini'}
                  onChange={() => onSelectProvider('gemini')}
                />
              </div>
              <div className="whatsapp-provider-card__info">
                <span className="whatsapp-provider-card__title">Google Cloud Gemini</span>
                <span className="whatsapp-provider-card__sub">Gemini 2.5 / 1.5 Flash (Multimodal nativo)</span>
              </div>
            </div>

            {/* Tarjeta OpenRouter */}
            <div
              className={`whatsapp-provider-card ${activeProvider === 'openrouter' ? 'whatsapp-provider-card--active' : ''}`}
              onClick={() => onSelectProvider('openrouter')}
            >
              <div className="whatsapp-provider-card__radio">
                <input
                  type="radio"
                  name="ai_provider"
                  checked={activeProvider === 'openrouter'}
                  onChange={() => onSelectProvider('openrouter')}
                />
              </div>
              <div className="whatsapp-provider-card__info">
                <span className="whatsapp-provider-card__title">OpenRouter API</span>
                <span className="whatsapp-provider-card__sub">Modelos unificados (Gemini Flash / Claude / Llama)</span>
              </div>
            </div>

            {/* Tarjeta Kimi */}
            <div
              className={`whatsapp-provider-card ${activeProvider === 'kimi' ? 'whatsapp-provider-card--active' : ''}`}
              onClick={() => onSelectProvider('kimi')}
            >
              <div className="whatsapp-provider-card__radio">
                <input
                  type="radio"
                  name="ai_provider"
                  checked={activeProvider === 'kimi'}
                  onChange={() => onSelectProvider('kimi')}
                />
              </div>
              <div className="whatsapp-provider-card__info">
                <span className="whatsapp-provider-card__title">Kimi (Moonshot AI)</span>
                <span className="whatsapp-provider-card__sub">moonshot-v1-8k / Vision Preview (Soporte de imagen)</span>
              </div>
            </div>
          </div>

          <div className="whatsapp-modal__keys-section">
            <label className="whatsapp-key-label">
              <span>API Key personalizada de Gemini</span>
              <input
                type="password"
                placeholder="Dejar vacio para usar la clave del servidor..."
                value={localGeminiKey}
                onChange={e => setLocalGeminiKey(e.target.value)}
                className="whatsapp-key-input"
              />
            </label>

            <label className="whatsapp-key-label">
              <span>API Key personalizada de OpenRouter</span>
              <input
                type="password"
                placeholder="Dejar vacio para usar la clave del servidor..."
                value={localOpenrouterKey}
                onChange={e => setLocalOpenrouterKey(e.target.value)}
                className="whatsapp-key-input"
              />
            </label>

            <label className="whatsapp-key-label">
              <span>API Key personalizada de Kimi / Moonshot</span>
              <input
                type="password"
                placeholder="Dejar vacio para usar la clave del servidor..."
                value={localKimiKey}
                onChange={e => setLocalKimiKey(e.target.value)}
                className="whatsapp-key-input"
              />
            </label>
          </div>
        </div>

        <div className="whatsapp-modal__footer">
          <button type="button" className="whatsapp-btn-cancel" onClick={onClose}>
            Cancelar
          </button>
          <button type="button" className="whatsapp-btn-save" onClick={handleSave}>
            Guardar Configuracion
          </button>
        </div>
      </div>
    </div>
  );
};
