import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../../shared/components/ui/Widget';
import { AuthLayout } from '../../shared/AuthLayout';
import { apiFetch } from '../../../../shared/lib/api';

export const ResetPasswordView: React.FC = () => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [email, setEmail] = useState('');
  const [codigo, setCodigo] = useState('');
  const [nuevaPassword, setNuevaPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    try {
      await apiFetch('/usuarios/recuperar-password/solicitar', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      setStep(2);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (code: string) => {
    setCodigo(code);
    setIsLoading(true);
    setErrorMsg('');
    try {
      await apiFetch('/usuarios/recuperar-password/verificar', {
        method: 'POST',
        body: JSON.stringify({ email, codigo: code }),
      });
      setStep(3);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (nuevaPassword !== confirmPassword) {
      setErrorMsg('Las contraseñas no coinciden.');
      return;
    }
    setIsLoading(true);
    setErrorMsg('');
    try {
      await apiFetch('/usuarios/recuperar-password/reset', {
        method: 'POST',
        body: JSON.stringify({ email, codigo, nueva_password: nuevaPassword }),
      });
      alert('Contraseña restablecida correctamente.');
      navigate('/login');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const resetBackground = (
    <div style={{ position: 'absolute', width: '100%', height: '100%' }}>
      <Widget.Shapes.StripedSquare size={300} color="var(--primary)" animation="spin" style={{ position: 'absolute', top: '20%', left: '-5%', opacity: 0.15 }} />
      <Widget.Shapes.HalfCircle size={200} color="var(--accent)" style={{ position: 'absolute', bottom: '10%', right: '10%', opacity: 0.2 }} />
      <Widget.Shapes.DotsPattern size={150} color="var(--text-secondary)" animation="float" style={{ position: 'absolute', top: '10%', right: '20%', opacity: 0.15 }} />
      <Widget.Shapes.Grid size={300} color="var(--border-color)" animation="pulse" style={{ position: 'absolute', top: '40%', left: '30%', opacity: 0.2 }} />
      <Widget.Shapes.Triangle size={120} color="var(--secondary)" animation="spin" style={{ position: 'absolute', bottom: '30%', left: '10%', opacity: 0.15 }} />
    </div>
  );

  return (
    <AuthLayout 
      title="RECUPERAR" 
      subtitle={
        step === 1 ? "Ingresa tu correo para recibir un código de acceso." : 
        step === 2 ? "Ingresa el código de 6 dígitos enviado a tu correo." : 
        "Crea una nueva contraseña segura."
      }
      backgroundShapes={resetBackground}
    >
      {errorMsg && <div style={{ color: 'var(--accent)', fontSize: '0.9rem', textAlign: 'center', marginBottom: '1rem' }}>{errorMsg}</div>}
      {step === 1 && (
        <Widget.Animation.FadeIn delay={0.1} direction="up" key="step1">
          <form onSubmit={handleSendEmail} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Widget.Input.Primary 
              type="email" 
              placeholder="correo@ejemplo.com" 
              label="CORREO ELECTRÓNICO"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <div className="auth-actions">
              <Widget.Button.Primary type="submit" isLoading={isLoading} className="auth-btn-massive">
                ENVIAR CÓDIGO
              </Widget.Button.Primary>
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
                <Widget.Button.Ghost type="button" onClick={() => navigate('/login')}>
                  Volver al inicio de sesión
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
            <Widget.Input.OTP length={6} onComplete={handleVerifyOTP} />
            {isLoading && <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Verificando...</p>}
          </div>
        </Widget.Animation.FadeIn>
      )}

      {step === 3 && (
        <Widget.Animation.FadeIn delay={0.1} direction="up" key="step3">
          <form onSubmit={handleResetPassword} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <Widget.Input.Primary 
              type="password" 
              placeholder="••••••••" 
              label="NUEVA CONTRASEÑA"
              value={nuevaPassword}
              onChange={(e) => setNuevaPassword(e.target.value)}
              required
            />
            <Widget.Input.Secondary 
              type="password" 
              placeholder="••••••••" 
              label="CONFIRMAR CONTRASEÑA"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            <div className="auth-actions">
              <Widget.Button.Primary type="submit" isLoading={isLoading} className="auth-btn-massive">
                ACTUALIZAR CONTRASEÑA
              </Widget.Button.Primary>
            </div>
          </form>
        </Widget.Animation.FadeIn>
      )}
    </AuthLayout>
  );
};
