import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { configApi } from '../services/config_api';
import { API_URL, apiFetch } from '@/shared/lib/api';
import './ConfiguracionView.css';

type ConfigTab = 'cuenta' | 'recuperar' | 'host' | 'github' | 'preferencias';

export const ConfiguracionView: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get('tab') as ConfigTab) || 'cuenta';
  const [activeTab, setActiveTab] = useState<ConfigTab>(initialTab);

  // Profile and status state
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [githubVinculado, setGithubVinculado] = useState(false);
  const [githubUsername, setGithubUsername] = useState<string | null>(null);
  const [dbConfigurada, setDbConfigurada] = useState(false);

  // Host DB password state
  const [requestingOtpDb, setRequestingOtpDb] = useState(false);
  const [otpSentDb, setOtpSentDb] = useState(false);
  const [otpCodeDb, setOtpCodeDb] = useState('');
  const [dbPassword, setDbPassword] = useState('');
  const [savingDb, setSavingDb] = useState(false);

  // GitHub unlinking state
  const [unlinkingGithub, setUnlinkingGithub] = useState(false);

  // Password reset state (Cuenta)
  const [resetStep, setResetStep] = useState<1 | 2 | 3>(1);
  const [resetEmail, setResetEmail] = useState('');
  const [resetOtp, setResetOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  // Notification banners
  const [banner, setBanner] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchConfig = async () => {
    try {
      const config = await configApi.obtenerConfiguracion();
      setGithubVinculado(config.github_vinculado);
      setGithubUsername(config.github_username);
      setDbConfigurada(config.db_configurada);
      setUserEmail(config.email || null);
      if (config.email) {
        setResetEmail(config.email);
      }
    } catch {
      setBanner({ type: 'error', text: 'Error al cargar la configuración de perfil.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  // Handlers for Host DB Password
  const handleSolicitarOtpDb = async () => {
    setRequestingOtpDb(true);
    setBanner(null);
    try {
      await configApi.solicitarOtpDb();
      setOtpSentDb(true);
      setBanner({ type: 'success', text: `Código OTP de 6 dígitos enviado a ${userEmail || 'tu correo'}.` });
    } catch (err: any) {
      setBanner({ type: 'error', text: err.message || 'Error al solicitar código OTP.' });
    } finally {
      setRequestingOtpDb(false);
    }
  };

  const handleSaveDbPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCodeDb.trim()) {
      setBanner({ type: 'error', text: 'Por favor ingresa el código OTP recibido en tu correo.' });
      return;
    }
    if (!dbPassword || dbPassword.length < 4) {
      setBanner({ type: 'error', text: 'La contraseña de la BD debe tener al menos 4 caracteres.' });
      return;
    }

    setSavingDb(true);
    setBanner(null);
    try {
      await configApi.configurarDbPassword(dbPassword, otpCodeDb.trim());
      setDbConfigurada(true);
      setDbPassword('');
      setOtpCodeDb('');
      setOtpSentDb(false);
      setBanner({ type: 'success', text: '¡Contraseña de Base de Datos PostgreSQL actualizada en el Host!' });
    } catch (err: any) {
      setBanner({ type: 'error', text: err.message || 'Error al actualizar la contraseña de la BD.' });
    } finally {
      setSavingDb(false);
    }
  };

  // Handlers for GitHub
  const handleIniciarVinculacionGithub = async () => {
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
    } catch {
      setBanner({ type: 'error', text: 'Error al iniciar vinculación con GitHub.' });
    }
  };

  const handleDesvincularGithub = async () => {
    if (!window.confirm("¿Deseas desvincular tu cuenta de GitHub? Se revertirán los permisos de exportación automática.")) {
      return;
    }

    setUnlinkingGithub(true);
    setBanner(null);
    try {
      await configApi.desvincularGithub();
      setGithubVinculado(false);
      setGithubUsername(null);
      setBanner({ type: 'success', text: 'Cuenta de GitHub desvinculada exitosamente.' });
    } catch (err: any) {
      setBanner({ type: 'error', text: err.message || 'Error al desvincular GitHub.' });
    } finally {
      setUnlinkingGithub(false);
    }
  };

  // Handlers for Reset Account Password
  const handleSendResetEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetLoading(true);
    setBanner(null);
    try {
      await apiFetch('/usuarios/recuperar-password/solicitar', {
        method: 'POST',
        body: JSON.stringify({ email: resetEmail }),
      });
      setResetStep(2);
      setBanner({ type: 'success', text: `Código de verificación enviado a ${resetEmail}. Revisa tu correo.` });
    } catch (err: any) {
      setBanner({ type: 'error', text: err.message || 'Error al solicitar cambio de contraseña.' });
    } finally {
      setResetLoading(false);
    }
  };

  const handleVerifyResetOtp = async (code: string) => {
    setResetOtp(code);
    setResetLoading(true);
    setBanner(null);
    try {
      await apiFetch('/usuarios/recuperar-password/verificar', {
        method: 'POST',
        body: JSON.stringify({ email: resetEmail, codigo: code }),
      });
      setResetStep(3);
      setBanner({ type: 'success', text: 'Código verificado correctamente. Ingresa la nueva contraseña.' });
    } catch (err: any) {
      setBanner({ type: 'error', text: err.message || 'Código inválido o expirado.' });
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setBanner({ type: 'error', text: 'Las contraseñas no coinciden.' });
      return;
    }
    setResetLoading(true);
    setBanner(null);
    try {
      await apiFetch('/usuarios/recuperar-password/reset', {
        method: 'POST',
        body: JSON.stringify({ email: resetEmail, codigo: resetOtp, nueva_password: newPassword }),
      });
      setBanner({ type: 'success', text: '¡Contraseña de cuenta restablecida exitosamente!' });
      setResetStep(1);
      setNewPassword('');
      setConfirmPassword('');
      setResetOtp('');
    } catch (err: any) {
      setBanner({ type: 'error', text: err.message || 'Error al actualizar contraseña.' });
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className="config-page">
      {/* Top Navbar Header */}
      <header className="config-navbar">
        <div className="config-navbar-left">
          <button className="config-back-btn" onClick={() => navigate('/dashboard')} title="Volver al Dashboard">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
            <span>Volver</span>
          </button>
          <div className="config-navbar-title">
            <h1>CONFIGURACIÓN DE LA CUENTA</h1>
            <p>Administra tu perfil, credenciales de PostgreSQL host e integraciones</p>
          </div>
        </div>

        <div className="config-navbar-right">
          {userEmail && (
            <div className="config-user-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              <span>{userEmail}</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Layout Container */}
      <div className="config-container">
        {/* Left Sidebar Panel */}
        <aside className="config-sidebar">
          <div className="sidebar-section-label">CUENTA & SEGURIDAD</div>
          <button
            className={`sidebar-nav-btn ${activeTab === 'cuenta' ? 'active' : ''}`}
            onClick={() => { setActiveTab('cuenta'); setBanner(null); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span>Información de Perfil</span>
          </button>

          <button
            className={`sidebar-nav-btn ${activeTab === 'recuperar' ? 'active' : ''}`}
            onClick={() => { setActiveTab('recuperar'); setBanner(null); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <span>Recuperar Contraseña</span>
          </button>

          <div className="sidebar-section-label">INFRAESTRUCTURA HOST</div>
          <button
            className={`sidebar-nav-btn ${activeTab === 'host' ? 'active' : ''}`}
            onClick={() => { setActiveTab('host'); setBanner(null); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
            <span>Contraseña BD PostgreSQL</span>
            {dbConfigurada && <span className="nav-status-dot online" title="BD Configurada" />}
          </button>

          <div className="sidebar-section-label">INTEGRACIONES</div>
          <button
            className={`sidebar-nav-btn ${activeTab === 'github' ? 'active' : ''}`}
            onClick={() => { setActiveTab('github'); setBanner(null); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
            <span>Vincular con GitHub</span>
            {githubVinculado && <span className="nav-status-badge">@ {githubUsername}</span>}
          </button>

          <div className="sidebar-section-label">SISTEMA</div>
          <button
            className={`sidebar-nav-btn ${activeTab === 'preferencias' ? 'active' : ''}`}
            onClick={() => { setActiveTab('preferencias'); setBanner(null); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            <span>Preferencias del Sistema</span>
          </button>
        </aside>

        {/* Right Main Content Area */}
        <main className="config-content-area">
          {banner && (
            <div className={`config-banner config-banner--${banner.type}`}>
              {banner.type === 'success' ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              )}
              <span>{banner.text}</span>
            </div>
          )}

          {loading ? (
            <div className="config-loading-state">
              <div className="config-spinner" />
              <p>Cargando información del perfil...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: Informacion de Perfil */}
              {activeTab === 'cuenta' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Información de Cuenta</h2>
                    <p>Detalles de registro y credenciales de acceso al sistema.</p>
                  </div>

                  <div className="config-card">
                    <div className="field-row">
                      <label>Correo Electrónico Registrado</label>
                      <input type="email" value={userEmail || ''} readOnly className="config-input readonly" />
                    </div>

                    <div className="field-row">
                      <label>Estado de la Cuenta</label>
                      <div className="status-pill active">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Usuario Activo & Autenticado</span>
                      </div>
                    </div>

                    <div className="card-actions-row">
                      <button className="btn-secondary" onClick={() => setActiveTab('recuperar')}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                        <span>Cambiar Contraseña de Cuenta</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: Recuperar / Cambiar Contrasena */}
              {activeTab === 'recuperar' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Recuperar / Cambiar Contraseña de Cuenta</h2>
                    <p>Proceso seguro de verificación por código OTP enviado a tu correo.</p>
                  </div>

                  <div className="config-card">
                    {resetStep === 1 && (
                      <form onSubmit={handleSendResetEmail} className="config-form">
                        <p className="hint-text">
                          Para modificar la contraseña de tu cuenta, confirma tu correo electrónico para enviarte un código OTP de 6 dígitos.
                        </p>
                        <div className="field-group">
                          <label>Correo Electrónico</label>
                          <input
                            type="email"
                            className="config-input"
                            value={resetEmail}
                            onChange={(e) => setResetEmail(e.target.value)}
                            required
                          />
                        </div>

                        <button type="submit" className="btn-primary" disabled={resetLoading}>
                          {resetLoading ? 'Enviando código...' : 'Solicitar Código OTP de Verificación'}
                        </button>
                      </form>
                    )}

                    {resetStep === 2 && (
                      <div className="config-form">
                        <p className="hint-text">
                          Ingresa el código OTP de 6 dígitos que fue enviado a <strong>{resetEmail}</strong>.
                        </p>
                        <div className="field-group">
                          <label>Código OTP de 6 Dígitos</label>
                          <input
                            type="text"
                            maxLength={6}
                            className="config-input code-input"
                            placeholder="Ej. 123456"
                            value={resetOtp}
                            onChange={(e) => {
                              const val = e.target.value;
                              setResetOtp(val);
                              if (val.length === 6) {
                                handleVerifyResetOtp(val);
                              }
                            }}
                          />
                        </div>

                        <div className="btn-group-row">
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => handleVerifyResetOtp(resetOtp)}
                            disabled={resetLoading || resetOtp.length < 6}
                          >
                            {resetLoading ? 'Verificando...' : 'Verificar Código OTP'}
                          </button>
                          <button type="button" className="btn-link" onClick={() => setResetStep(1)}>
                            Reenviar o Cambiar Correo
                          </button>
                        </div>
                      </div>
                    )}

                    {resetStep === 3 && (
                      <form onSubmit={handleResetPassword} className="config-form">
                        <div className="field-group">
                          <label>Nueva Contraseña</label>
                          <input
                            type="password"
                            className="config-input"
                            placeholder="Mínimo 6 caracteres"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            required
                          />
                        </div>

                        <div className="field-group">
                          <label>Confirmar Nueva Contraseña</label>
                          <input
                            type="password"
                            className="config-input"
                            placeholder="Repite la nueva contraseña"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                          />
                        </div>

                        <button type="submit" className="btn-primary" disabled={resetLoading}>
                          {resetLoading ? 'Actualizando...' : 'Establecer Nueva Contraseña'}
                        </button>
                      </form>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 3: Contrasena de Base de Datos Host */}
              {activeTab === 'host' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Contraseña de Base de Datos (Host)</h2>
                    <p>Asigna o cambia la contraseña de tu usuario PostgreSQL en <code>db.gerlextech.com</code>.</p>
                  </div>

                  <div className="config-card">
                    {dbConfigurada ? (
                      <div className="info-box-success">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                        <div>
                          <strong>Base de Datos Configurada</strong>
                          <p>Tu usuario PostgreSQL en el host tiene contraseña activa. Puedes actualizarla solicitando un nuevo código OTP.</p>
                        </div>
                      </div>
                    ) : (
                      <div className="info-box-warning">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        <div>
                          <strong>Contraseña Pendiente de Configuración</strong>
                          <p>Asigna tu contraseña para habilitar el acceso PostgreSQL externo a los esquemas de tus proyectos.</p>
                        </div>
                      </div>
                    )}

                    <form onSubmit={handleSaveDbPassword} className="config-form">
                      {!otpSentDb ? (
                        <div className="step-container">
                          <div className="step-label">Paso 1: Verificación de Identidad</div>
                          <p className="hint-text">Solicita un código OTP enviado a tu correo <strong>{userEmail}</strong> para autorizar la actualización en la BD del host.</p>
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={handleSolicitarOtpDb}
                            disabled={requestingOtpDb}
                          >
                            {requestingOtpDb ? 'Enviando OTP...' : 'Solicitar Código OTP por Correo'}
                          </button>
                        </div>
                      ) : (
                        <div className="step-container">
                          <div className="step-label">Paso 2: Ingresar Código y Nueva Contraseña</div>
                          <div className="field-group">
                            <label>CÓDIGO DE VERIFICACIÓN OTP (6 DÍGITOS)</label>
                            <input
                              type="text"
                              maxLength={6}
                              className="config-input code-input"
                              placeholder="Ej. 654321"
                              value={otpCodeDb}
                              onChange={(e) => setOtpCodeDb(e.target.value)}
                              required
                            />
                          </div>

                          <div className="field-group">
                            <label>NUEVA CONTRASEÑA DE BASE DE DATOS (POSTGRESQL)</label>
                            <input
                              type="password"
                              className="config-input"
                              placeholder="Mínimo 4 caracteres"
                              value={dbPassword}
                              onChange={(e) => setDbPassword(e.target.value)}
                              required
                            />
                          </div>

                          <div className="btn-group-row">
                            <button type="submit" className="btn-primary" disabled={savingDb}>
                              {savingDb ? 'Guardando en Host...' : 'Actualizar Contraseña de BD'}
                            </button>
                            <button type="button" className="btn-link" onClick={() => setOtpSentDb(false)}>
                              Cancelar
                            </button>
                          </div>
                        </div>
                      )}
                    </form>
                  </div>
                </div>
              )}

              {/* TAB 4: Vincular / Desvincular GitHub */}
              {activeTab === 'github' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Vinculación con GitHub</h2>
                    <p>Permite a la aplicación exportar repositorios y realizar despliegues automáticos en tu cuenta de GitHub.</p>
                  </div>

                  <div className="config-card">
                    {githubVinculado ? (
                      <div className="github-card-status linked">
                        <div className="github-card-header">
                          <div className="github-icon-badge">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                          </div>
                          <div>
                            <h3>Cuenta de GitHub Vinculada</h3>
                            <p className="github-handle">Usuario: <strong>@{githubUsername}</strong></p>
                          </div>
                        </div>

                        <p className="hint-text">
                          Tu cuenta está autorizada para exportar el código fuente Java/Spring Boot generado por IA y crear repositorios de manera directa.
                        </p>

                        <button
                          type="button"
                          className="btn-danger"
                          onClick={handleDesvincularGithub}
                          disabled={unlinkingGithub}
                        >
                          {unlinkingGithub ? 'Desvinculando...' : 'Desvincular Cuenta de GitHub'}
                        </button>
                      </div>
                    ) : (
                      <div className="github-card-status unlinked">
                        <div className="github-card-header">
                          <div className="github-icon-badge muted">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                          </div>
                          <div>
                            <h3>Sin Cuenta de GitHub Vinculada</h3>
                            <p className="hint-text">Vincula tu cuenta OAuth para habilitar la exportación automática de código y auto-despliegue.</p>
                          </div>
                        </div>

                        <button
                          type="button"
                          className="btn-primary"
                          onClick={handleIniciarVinculacionGithub}
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                          <span>Vincular Cuenta con GitHub</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 5: Preferencias de Sistema */}
              {activeTab === 'preferencias' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Preferencias del Sistema</h2>
                    <p>Opciones generales del entorno de trabajo y persistencia local.</p>
                  </div>

                  <div className="config-card">
                    <div className="pref-row">
                      <div>
                        <strong>Tema del Entorno</strong>
                        <p>Paleta oscura de alto contraste (Gerlextech Premium Dark).</p>
                      </div>
                      <span className="pref-badge">Oscuro (Predeterminado)</span>
                    </div>

                    <div className="pref-row">
                      <div>
                        <strong>Persistencia Offline (IndexedDB)</strong>
                        <p>Los diagramas se sincronizan localmente en almacenamiento del navegador.</p>
                      </div>
                      <span className="pref-badge active">Activo</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};
