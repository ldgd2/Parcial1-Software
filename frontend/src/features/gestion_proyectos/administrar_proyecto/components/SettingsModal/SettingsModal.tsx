import React, { useState, useEffect } from 'react';
import { configApi } from '@/features/gestion_usuarios/configurar_perfil/services/config_api';
import { API_URL } from '@/shared/lib/api';
import './SettingsModal.css';

interface Props {
  onClose: () => void;
}

export const SettingsModal: React.FC<Props> = ({ onClose }) => {
  const [githubVinculado, setGithubVinculado] = useState(false);
  const [githubUsername, setGithubUsername] = useState<string | null>(null);
  const [dbConfigurada, setDbConfigurada] = useState(false);
  const [dbPassword, setDbPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await configApi.obtenerConfiguracion();
        setGithubVinculado(config.github_vinculado);
        setGithubUsername(config.github_username);
        setDbConfigurada(config.db_configurada);
      } catch (err) {
        setMessage({ type: 'error', text: 'Error al cargar la configuración.' });
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleSaveDb = async () => {
    if (!dbPassword) {
      setMessage({ type: 'error', text: 'La contraseña no puede estar vacía.' });
      return;
    }
    setSaving(true);
    try {
      await configApi.configurarDbPassword(dbPassword);
      setDbConfigurada(true);
      setDbPassword('');
      setMessage({ type: 'success', text: '¡Contraseña guardada con éxito!' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Error al guardar la contraseña.' });
    } finally {
      setSaving(false);
    }
  };

  const iniciarVinculacion = async () => {
      try {
          const res = await fetch(`${API_URL}/exportar-github/auth-url`, {
              headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
          });
          const data = await res.json();
          if (data.url) {
              window.location.href = data.url;
          }
      } catch (err) {
          setMessage({ type: 'error', text: 'Error iniciando vinculación con GitHub' });
      }
  };

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal-content">
        <div className="settings-modal-header">
          <h2>Configuración de Despliegue Global</h2>
          <button className="settings-close-btn" onClick={onClose}>&times;</button>
        </div>

        {message && (
          <div className={`settings-alert settings-alert--${message.type}`}>
            {message.text}
          </div>
        )}

        {loading ? (
          <div className="settings-loading">Cargando...</div>
        ) : (
          <div className="settings-body">
            
            <div className="settings-section">
              <h3>1. Vinculación con GitHub</h3>
              <p>Necesario para exportar el código fuente de tus proyectos.</p>
              {githubVinculado ? (
                <div className="settings-status-card success">
                  <span className="status-icon">✓</span>
                  <span>Conectado como <strong>{githubUsername}</strong></span>
                </div>
              ) : (
                <button className="settings-btn-primary" onClick={iniciarVinculacion}>
                  Conectar cuenta de GitHub
                </button>
              )}
            </div>

            <div className="settings-section">
              <h3>2. Auto-Alojamiento (Base de Datos)</h3>
              <p>Configura la contraseña de tu cuenta para la base de datos PostgreSQL generada. Se usará tu correo como usuario.</p>
              
              {dbConfigurada && (
                <div className="settings-status-card success" style={{ marginBottom: 15 }}>
                  <span className="status-icon">✓</span>
                  <span>Ya tienes una contraseña guardada. Puedes cambiarla abajo.</span>
                </div>
              )}

              <div className="settings-form-group">
                <label>Nueva Contraseña de Base de Datos</label>
                <input 
                  type="password" 
                  placeholder="Ingresa una contraseña segura"
                  value={dbPassword}
                  onChange={(e) => setDbPassword(e.target.value)}
                />
              </div>
              <button 
                className="settings-btn-primary" 
                onClick={handleSaveDb} 
                disabled={saving || !dbPassword}
              >
                {saving ? 'Guardando...' : 'Guardar Contraseña de DB'}
              </button>
            </div>

          </div>
        )}
      </div>
    </div>
  );
};
