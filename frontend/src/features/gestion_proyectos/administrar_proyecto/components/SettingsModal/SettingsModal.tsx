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
  const [userEmail, setUserEmail] = useState<string | null>(null);
  
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [dbPassword, setDbPassword] = useState('');
  
  const [loading, setLoading] = useState(true);
  const [unlinkingGithub, setUnlinkingGithub] = useState(false);
  const [requestingOtp, setRequestingOtp] = useState(false);
  const [savingDb, setSavingDb] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const fetchConfig = async () => {
    try {
      const config = await configApi.obtenerConfiguracion();
      setGithubVinculado(config.github_vinculado);
      setGithubUsername(config.github_username);
      setDbConfigurada(config.db_configurada);
      setUserEmail(config.email || null);
    } catch (err) {
      setMessage({ type: 'error', text: 'Error al cargar la configuración de perfil.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSolicitarOtp = async () => {
    setRequestingOtp(true);
    setMessage(null);
    try {
      await configApi.solicitarOtpDb();
      setOtpSent(true);
      setMessage({ type: 'success', text: `Código OTP enviado a ${userEmail || 'tu correo'}. Revisa tu bandeja de entrada.` });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error al solicitar código OTP.' });
    } finally {
      setRequestingOtp(false);
    }
  };

  const handleSaveDb = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode.trim()) {
      setMessage({ type: 'error', text: 'Por favor ingresa el código OTP de 6 dígitos.' });
      return;
    }
    if (!dbPassword || dbPassword.length < 4) {
      setMessage({ type: 'error', text: 'La contraseña de la BD debe tener al menos 4 caracteres.' });
      return;
    }

    setSavingDb(true);
    setMessage(null);
    try {
      await configApi.configurarDbPassword(dbPassword, otpCode.trim());
      setDbConfigurada(true);
      setDbPassword('');
      setOtpCode('');
      setOtpSent(false);
      setMessage({ type: 'success', text: '¡Contraseña de Base de Datos actualizada exitosamente en el Host!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error al actualizar la contraseña de la BD.' });
    } finally {
      setSavingDb(false);
    }
  };

  const handleInicarchVinculacion = async () => {
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
      setMessage({ type: 'error', text: 'Error al iniciar vinculación con GitHub' });
    }
  };

  const handleDesvincularGithub = async () => {
    if (!window.confirm("¿Seguro que deseas desvincular tu cuenta de GitHub? Ya no podrás exportar proyectos hasta que la vuelvas a vincular.")) {
      return;
    }

    setUnlinkingGithub(true);
    setMessage(null);
    try {
      await configApi.desvincularGithub();
      setGithubVinculado(false);
      setGithubUsername(null);
      setMessage({ type: 'success', text: 'Cuenta de GitHub desvinculada exitosamente.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error al desvincular GitHub.' });
    } finally {
      setUnlinkingGithub(false);
    }
  };

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal-card">
        {/* Header Fijo */}
        <div className="settings-modal-header">
          <div className="settings-modal-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            <h2>CONFIGURACIÓN DE LA CUENTA</h2>
          </div>
          <button className="settings-modal-close" onClick={onClose} aria-label="Cerrar">&times;</button>
        </div>

        {/* Body Con Scrollbar Integrado */}
        <div className="settings-modal-body">
          {message && (
            <div className={`settings-banner settings-banner--${message.type}`}>
              {message.type === 'success' ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              )}
              <span>{message.text}</span>
            </div>
          )}

          {loading ? (
            <div className="settings-loading-box">
              <span className="settings-spinner" />
              <span>Cargando perfil...</span>
            </div>
          ) : (
            <div className="settings-sections">
              {/* Sección 1: Vinculación de GitHub */}
              <div className="settings-card-section">
                <div className="section-header">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                  <div>
                    <h3>1. VINCULACIÓN CON GITHUB</h3>
                    <p>Requerido para la exportación y despliegue automático del código fuente Java/Spring Boot.</p>
                  </div>
                </div>

                {githubVinculado ? (
                  <div className="github-status-box linked">
                    <div className="github-user-info">
                      <div className="github-avatar-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                      </div>
                      <div>
                        <span className="github-status-label">Cuenta Vinculada</span>
                        <strong className="github-username">@{githubUsername}</strong>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="settings-btn-danger"
                      onClick={handleDesvincularGithub}
                      disabled={unlinkingGithub}
                    >
                      {unlinkingGithub ? 'Desvinculando...' : 'Desvincular GitHub'}
                    </button>
                  </div>
                ) : (
                  <div className="github-status-box unlinked">
                    <p className="unlinked-hint">No tienes una cuenta de GitHub asociada a tu perfil.</p>
                    <button
                      type="button"
                      className="settings-btn-primary"
                      onClick={handleInicarchVinculacion}
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                      <span>Vincular Cuenta de GitHub</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Sección 2: Base de Datos PostgreSQL Host */}
              <div className="settings-card-section">
                <div className="section-header">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                  <div>
                    <h3>2. CONTRASEÑA DE BASE DE DATOS (HOST)</h3>
                    <p>Contraseña asignada a tu usuario PostgreSQL en Gerlextech Host. Requiere verificación OTP por correo.</p>
                  </div>
                </div>

                {dbConfigurada && (
                  <div className="settings-badge-info">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                    <span>Tu base de datos en el host tiene contraseña configurada. Puedes cambiarla solicitando un nuevo código OTP.</span>
                  </div>
                )}

                <form onSubmit={handleSaveDb} className="settings-form">
                  {!otpSent ? (
                    <div className="otp-request-box">
                      <p className="otp-hint">Paso 1: Solicita un código de verificación OTP a tu correo <strong>{userEmail || ''}</strong>.</p>
                      <button
                        type="button"
                        className="settings-btn-secondary"
                        onClick={handleSolicitarOtp}
                        disabled={requestingOtp}
                      >
                        {requestingOtp ? (
                          <>
                            <span className="settings-spinner-sm" />
                            <span>Enviando OTP...</span>
                          </>
                        ) : (
                          <>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                            <span>Solicitar Código OTP por Correo</span>
                          </>
                        )}
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="settings-field">
                        <label>CÓDIGO DE VERIFICACIÓN OTP</label>
                        <input
                          type="text"
                          maxLength={6}
                          placeholder="Código de 6 dígitos"
                          value={otpCode}
                          onChange={(e) => setOtpCode(e.target.value)}
                          required
                        />
                      </div>

                      <div className="settings-field">
                        <label>NUEVA CONTRASEÑA DE BASE DE DATOS</label>
                        <input
                          type="password"
                          placeholder="Mínimo 4 caracteres"
                          value={dbPassword}
                          onChange={(e) => setDbPassword(e.target.value)}
                          required
                        />
                      </div>

                      <div className="settings-actions">
                        <button
                          type="button"
                          className="settings-btn-text"
                          onClick={() => setOtpSent(false)}
                        >
                          Reenviar OTP
                        </button>
                        <button
                          type="submit"
                          className="settings-btn-primary"
                          disabled={savingDb || !otpCode || !dbPassword}
                        >
                          {savingDb ? 'Guardando...' : 'Actualizar en Host'}
                        </button>
                      </div>
                    </>
                  )}
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
