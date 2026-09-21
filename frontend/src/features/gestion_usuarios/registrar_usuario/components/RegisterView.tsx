import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../../shared/components/ui/Widget';
import { AuthLayout } from '../../shared/AuthLayout';
import { apiFetch } from '../../../../shared/lib/api';
import { TokenService } from '../../../../shared/lib/TokenService';
import { actualizarHabilidades } from '@/features/gestion_asistencia_ia/gestionar_equipo_ia/services/equipoService';

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

export const RegisterView: React.FC = () => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Step 3: habilidades
  const [etiquetasSeleccionadas, setEtiquetasSeleccionadas] = useState<string[]>([]);
  const [etiquetaCustom, setEtiquetaCustom] = useState('');

  const navigate = useNavigate();

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

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    try {
      await apiFetch('/usuarios/registro/solicitar-otp', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      setStep(2);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyAndRegister = async (code: string) => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const data = await apiFetch('/usuarios/registro', {
        method: 'POST',
        body: JSON.stringify({ nombre, email, password, codigo_otp: code }),
      });
      // Si el backend devuelve un token al registrar, guardarlo para poder llamar habilidades
      if (data?.access_token) {
        TokenService.setToken(data.access_token);
      }
      setStep(3);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error desconocido');
      setIsLoading(false);
    }
  };

  const handleGuardarHabilidades = async () => {
    setIsLoading(true);
    try {
      if (etiquetasSeleccionadas.length > 0) {
        await actualizarHabilidades(etiquetasSeleccionadas);
      }
    } catch {
      // silencioso: las habilidades son opcionales, no bloquear el registro
    } finally {
      setIsLoading(false);
      navigate('/login');
    }
  };

  const registerBackground = (
    <div style={{ position: 'absolute', width: '100%', height: '100%' }}>
      <Widget.Shapes.HalfCircle size={400} color="var(--secondary)" animation="pulse" style={{ position: 'absolute', top: '-10%', left: '-10%', opacity: 0.15 }} />
      <Widget.Shapes.DotsPattern size={300} color="var(--primary)" style={{ position: 'absolute', bottom: '20%', right: '10%', opacity: 0.15 }} />
      <Widget.Shapes.Circle size={150} color="var(--accent)" animation="float" style={{ position: 'absolute', top: '50%', right: '30%', opacity: 0.2 }} />
      <Widget.Shapes.Triangle size={180} color="var(--text-secondary)" animation="spin" style={{ position: 'absolute', bottom: '-5%', left: '20%', opacity: 0.1 }} />
      <Widget.Shapes.Grid size={250} color="var(--border-color)" style={{ position: 'absolute', top: '10%', right: '-5%', opacity: 0.25 }} />
    </div>
  );

  const subtitleMap = {
    1: 'Únete al sistema y comienza a diseñar.',
    2: 'Ingresa el código enviado a tu correo.',
    3: 'Cuéntanos en qué eres bueno (opcional).',
  };

  return (
    <AuthLayout
      title="REGISTRO"
      subtitle={subtitleMap[step]}
      backgroundShapes={registerBackground}
    >
      {errorMsg && <div style={{ color: 'var(--accent)', fontSize: '0.9rem', textAlign: 'center', marginBottom: '1rem' }}>{errorMsg}</div>}

      {step === 1 && (
        <Widget.Animation.FadeIn delay={0.1} direction="up" key="step1">
          <form onSubmit={handleRequestOTP} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Widget.Input.Primary
              type="text"
              placeholder="John Doe"
              label="NOMBRE COMPLETO"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />

            <Widget.Input.Primary
              type="email"
              placeholder="correo@ejemplo.com"
              label="CORREO ELECTRÓNICO"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Widget.Input.Secondary
              type="password"
              placeholder="••••••••"
              label="CONTRASEÑA"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <div className="auth-actions">
              <Widget.Button.Primary type="submit" isLoading={isLoading} className="auth-btn-massive">
                CONTINUAR
              </Widget.Button.Primary>

              <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
                <Widget.Button.Ghost type="button" onClick={() => navigate('/login')}>
                  ¿Ya tienes cuenta? Inicia sesión
                </Widget.Button.Ghost>
              </div>
            </div>
          </form>
        </Widget.Animation.FadeIn>
      )}

      {step === 2 && (
        <Widget.Animation.FadeIn delay={0.1} direction="up" key="step2">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', alignItems: 'center' }}>
            <label className="widget-input-label" style={{ width: '100%' }}>CÓDIGO DE VERIFICACIÓN</label>
            <Widget.Input.OTP length={6} onComplete={handleVerifyAndRegister} />
            {isLoading && <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Creando cuenta...</p>}
            <div style={{ marginTop: '1rem' }}>
              <Widget.Button.Ghost type="button" onClick={() => setStep(1)} disabled={isLoading}>
                Volver
              </Widget.Button.Ghost>
            </div>
          </div>
        </Widget.Animation.FadeIn>
      )}

      {step === 3 && (
        <Widget.Animation.FadeIn delay={0.1} direction="up" key="step3">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textAlign: 'center' }}>
              La IA usará tus habilidades para asignarte tareas acordes a tu perfil. Puedes editarlas después en Configuración.
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {ETIQUETAS_PREDEFINIDAS.map(tag => (
                <button
                  key={tag}
                  id={`reg-tag-${tag.replace(/\s/g, '-')}`}
                  type="button"
                  onClick={() => toggleEtiqueta(tag)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '20px',
                    border: etiquetasSeleccionadas.includes(tag) ? '1.5px solid var(--primary)' : '1.5px solid var(--border-color)',
                    background: etiquetasSeleccionadas.includes(tag) ? 'rgba(124,110,248,0.15)' : 'transparent',
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

            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
              <input
                id="input-reg-habilidad-custom"
                type="text"
                placeholder="Otra habilidad..."
                value={etiquetaCustom}
                onChange={e => setEtiquetaCustom(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && agregarCustom()}
                style={{
                  flex: 1,
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
              <Widget.Button.Ghost type="button" onClick={agregarCustom}>
                +
              </Widget.Button.Ghost>
            </div>

            <div className="auth-actions" style={{ marginTop: '8px' }}>
              <Widget.Button.Primary
                id="btn-finalizar-registro"
                type="button"
                isLoading={isLoading}
                className="auth-btn-massive"
                onClick={handleGuardarHabilidades}
              >
                {etiquetasSeleccionadas.length > 0 ? 'GUARDAR Y ENTRAR' : 'OMITIR Y ENTRAR'}
              </Widget.Button.Primary>
            </div>
          </div>
        </Widget.Animation.FadeIn>
      )}
    </AuthLayout>
  );
};
