import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { configApi } from '../services/config_api';
import { API_URL, apiFetch } from '@/shared/lib/api';
import { actualizarHabilidades } from '@/features/gestion_asistencia_ia/gestionar_equipo_ia/services/equipoService';
import './ConfiguracionView.css';

type ConfigTab = 'cuenta' | 'recuperar' | 'host' | 'github' | 'preferencias' | 'habilidades';

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

  // Habilidades IA state
  const ETIQUETAS_PREDEFINIDAS = [
    'backend', 'frontend', 'modelado', 'base de datos',
    'devops', 'ui/ux', 'mobile', 'seguridad', 'testing', 'arquitectura',
    'python', 'django', 'laravel', 'node.js', 'apis rest', 'graphql', 'websockets', 'orm', 'microservicios',
    'react', 'javascript', 'typescript', 'html5', 'css3', 'spa', 'pwa', 'responsive design',
    'flutter', 'dart', 'android', 'ios', 'react native',
    'postgresql', 'mysql', 'sql', 'nosql', 'mongodb', 'redis', 'migraciones', 'diagramas er',
    'vps', 'linux', 'ubuntu', 'aws', 'nginx', 'proxy inverso', 'docker', 'ci/cd', 'bash scripting', 'certificados ssl', 'balanceo de carga',
    'uml', 'mvc', 'patrones de diseño', 'clean architecture', 'ddd', 'serverless',
    'redes', 'hardware', 'iot', 'microcontroladores', 'tcp/ip'
  ];
  const [etiquetasSeleccionadas, setEtiquetasSeleccionadas] = useState<string[]>([]);
  const [etiquetaCustom, setEtiquetaCustom] = useState('');
  const [savingHabilidades, setSavingHabilidades] = useState(false);

  const toggleEtiqueta = (tag: string) => {
    setEtiquetasSeleccionadas(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const agregarCustom = () => {
    const trimmed = etiquetaCustom.trim().toLowerCase();
    if (trimmed && !etiquetasSeleccionadas.includes(trimmed)) {
      setEtiquetasSeleccionadas(prev => [...prev, trimmed]);
    }
    setEtiquetaCustom('');
  };

  const handleGuardarHabilidades = async () => {
    setSavingHabilidades(true);
    setBanner(null);
    try {
      await actualizarHabilidades(etiquetasSeleccionadas);
      setBanner({ type: 'success', text: 'Habilidades actualizadas correctamente.' });
    } catch {
      setBanner({ type: 'error', text: 'Error al guardar habilidades.' });
    } finally {
      setSavingHabilidades(false);
    }
  };

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

  // Browser Permissions State
  const [micPermissionStatus, setMicPermissionStatus] = useState<'prompt' | 'granted' | 'denied'>('prompt');
  const [notificationPermission, setNotificationPermission] = useState<'default' | 'granted' | 'denied'>('default');
  const [checkingMic, setCheckingMic] = useState(false);

  useEffect(() => {
    fetchConfig();
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: 'microphone' as PermissionName })
        .then((result) => {
          setMicPermissionStatus(result.state as any);
          result.onchange = () => setMicPermissionStatus(result.state as any);
        })
        .catch(() => {});
    }
  }, []);

  const handleSolicitarMicrofono = async () => {
    setCheckingMic(true);
    setBanner(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicPermissionStatus('granted');
      setBanner({ type: 'success', text: '¡Permiso de micrófono concedido exitosamente!' });
    } catch (err: any) {
      setMicPermissionStatus('denied');
      setBanner({ type: 'error', text: 'Permiso de micrófono denegado o no disponible en este dispositivo.' });
    } finally {
      setCheckingMic(false);
    }
  };

  const handleSolicitarNotificaciones = async () => {
    setBanner(null);
    if (!('Notification' in window)) {
      setBanner({ type: 'error', text: 'Este navegador no soporta notificaciones de escritorio.' });
      return;
    }
    try {
      const perm = await Notification.requestPermission();
      setNotificationPermission(perm);
      if (perm === 'granted') {
        setBanner({ type: 'success', text: '¡Notificaciones web concedidas correctamente!' });
      } else {
        setBanner({ type: 'error', text: 'Permiso de notificaciones denegado por el navegador.' });
      }
    } catch {
      setBanner({ type: 'error', text: 'Error al solicitar permisos de notificaciones.' });
    }
  };

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

          <div className="sidebar-section-label">IA & EQUIPO</div>
          <button
            className={`sidebar-nav-btn ${activeTab === 'habilidades' ? 'active' : ''}`}
            onClick={() => { setActiveTab('habilidades'); setBanner(null); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            <span>Habilidades de Desarrollador</span>
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

              {/* TAB 5: Preferencias de Sistema & Permisos del Navegador */}
              {activeTab === 'preferencias' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Preferencias del Sistema & Permisos</h2>
                    <p>Configura los accesos de hardware y navegador para audio, voz, archivos y notificaciones.</p>
                  </div>

                  <div className="config-card">
                    {/* Permiso de Micrófono / Audio */}
                    <div className="pref-row">
                      <div className="pref-info">
                        <div className="pref-icon">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
                        </div>
                        <div>
                          <strong>Permiso de Micrófono (Dictado por Voz)</strong>
                          <p>Permite enviar instrucciones y comandos de voz al Asistente IA para generar diagramas.</p>
                        </div>
                      </div>

                      <div className="pref-action">
                        {micPermissionStatus === 'granted' ? (
                          <span className="pref-badge active">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                            Concedido
                          </span>
                        ) : micPermissionStatus === 'denied' ? (
                          <span className="pref-badge danger">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            Denegado
                          </span>
                        ) : (
                          <span className="pref-badge">Pendiente</span>
                        )}

                        <button
                          type="button"
                          className="btn-secondary btn-sm"
                          onClick={handleSolicitarMicrofono}
                          disabled={checkingMic}
                        >
                          {checkingMic ? 'Probando...' : 'Activar / Probar Micrófono'}
                        </button>
                      </div>
                    </div>

                    {/* Permisos de Archivos & Carga */}
                    <div className="pref-row">
                      <div className="pref-info">
                        <div className="pref-icon">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        </div>
                        <div>
                          <strong>Subida & Exportación de Archivos</strong>
                          <p>Habilita la lectura de imágenes, archivos XML (Enterprise Architect) y JSON en el disco local.</p>
                        </div>
                      </div>

                      <div className="pref-action">
                        <span className="pref-badge active">Habilitado</span>
                      </div>
                    </div>

                    {/* Permisos de Notificaciones Web */}
                    <div className="pref-row">
                      <div className="pref-info">
                        <div className="pref-icon">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                        </div>
                        <div>
                          <strong>Notificaciones Web del Navegador</strong>
                          <p>Recibe avisos de aprobación de ingreso a salas y finalización de despliegues.</p>
                        </div>
                      </div>

                      <div className="pref-action">
                        {notificationPermission === 'granted' ? (
                          <span className="pref-badge active">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                            Concedido
                          </span>
                        ) : notificationPermission === 'denied' ? (
                          <span className="pref-badge danger">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            Denegado
                          </span>
                        ) : (
                          <span className="pref-badge">Pendiente</span>
                        )}

                        {notificationPermission !== 'granted' && (
                          <button
                            type="button"
                            className="btn-secondary btn-sm"
                            onClick={handleSolicitarNotificaciones}
                          >
                            Activar Notificaciones
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Tema & Persistencia */}
                    <div className="pref-row">
                      <div className="pref-info">
                        <div className="pref-icon">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
                        </div>
                        <div>
                          <strong>Tema del Entorno</strong>
                          <p>Paleta oscura de alto contraste (Gerlextech Premium Dark).</p>
                        </div>
                      </div>
                      <span className="pref-badge">Oscuro (Predeterminado)</span>
                    </div>

                    <div className="pref-row">
                      <div className="pref-info">
                        <div className="pref-icon">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                        </div>
                        <div>
                          <strong>Persistencia Offline (IndexedDB)</strong>
                          <p>Los diagramas se sincronizan automáticamente en almacenamiento IndexedDB local.</p>
                        </div>
                      </div>
                      <span className="pref-badge active">Activo</span>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB: Habilidades de Desarrollador */}
              {activeTab === 'habilidades' && (
                <div className="tab-pane fadeIn">
                  <div className="pane-header">
                    <h2>Habilidades de Desarrollador</h2>
                    <p>La IA usará estas etiquetas para asignarte tareas acordes a tu perfil técnico cuando el Anfitrión active el Gestor de Equipo.</p>
                  </div>

                  <div className="config-card">
                    <div className="field-row">
                      <label>Selecciona tus especialidades</label>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                        {ETIQUETAS_PREDEFINIDAS.map(tag => (
                          <button
                            key={tag}
                            id={`tag-${tag.replace(/\s/g, '-')}`}
                            type="button"
                            onClick={() => toggleEtiqueta(tag)}
                            style={{
                              padding: '6px 14px',
                              borderRadius: '20px',
                              border: etiquetasSeleccionadas.includes(tag) ? '1.5px solid var(--primary)' : '1.5px solid var(--border-color)',
                              background: etiquetasSeleccionadas.includes(tag) ? 'var(--surface-color)' : 'transparent',
                              color: etiquetasSeleccionadas.includes(tag) ? 'var(--primary)' : 'var(--text-secondary)',
                              fontSize: '12px',
                              fontWeight: 600,
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                              textTransform: 'uppercase',
                              letterSpacing: '0.06em',
                            }}
                          >
                            {tag}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="field-row" style={{ marginTop: '16px' }}>
                      <label>Agregar habilidad personalizada</label>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                        <input
                          id="input-habilidad-custom"
                          className="config-input"
                          type="text"
                          placeholder="ej: machine learning, microservicios..."
                          value={etiquetaCustom}
                          onChange={e => setEtiquetaCustom(e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && agregarCustom()}
                        />
                        <button className="btn-secondary" type="button" onClick={agregarCustom} id="btn-agregar-habilidad">
                          Agregar
                        </button>
                      </div>
                    </div>

                    {etiquetasSeleccionadas.length > 0 && (
                      <div className="field-row" style={{ marginTop: '16px' }}>
                        <label>Tu perfil actual</label>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                          {etiquetasSeleccionadas.map(tag => (
                            <span
                              key={tag}
                              style={{
                                display: 'inline-flex', alignItems: 'center', gap: '6px',
                                padding: '4px 12px', borderRadius: '20px',
                                background: 'var(--surface-color)', border: '1px solid var(--primary)', color: 'var(--primary)',
                                fontSize: '11px', fontWeight: 600,
                              }}
                            >
                              {tag}
                              <button
                                type="button"
                                onClick={() => toggleEtiqueta(tag)}
                                style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 0, lineHeight: 1 }}
                              >
                                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                              </button>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="card-actions-row" style={{ marginTop: '24px' }}>
                      <button
                        id="btn-guardar-habilidades"
                        className="btn-primary"
                        type="button"
                        onClick={handleGuardarHabilidades}
                        disabled={savingHabilidades || etiquetasSeleccionadas.length === 0}
                      >
                        {savingHabilidades ? 'Guardando...' : 'Guardar Habilidades'}
                      </button>
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
