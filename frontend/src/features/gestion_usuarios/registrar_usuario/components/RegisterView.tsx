import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../../shared/components/ui/Widget';
import { AuthLayout } from '../../shared/AuthLayout';
import { apiFetch } from '../../../../shared/lib/api';

export const RegisterView: React.FC = () => {
  const [step, setStep] = useState<1 | 2>(1);
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();

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
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyAndRegister = async (code: string) => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      await apiFetch('/usuarios/registro', {
        method: 'POST',
        body: JSON.stringify({ nombre, email, password, codigo_otp: code }),
      });
      alert('Registro Exitoso');
      navigate('/login');
    } catch (err: any) {
      setErrorMsg(err.message);
      setIsLoading(false);
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

  return (
    <AuthLayout 
      title="REGISTRO" 
      subtitle={step === 1 ? "Únete al sistema y comienza a diseñar." : "Ingresa el código enviado a tu correo."}
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
    </AuthLayout>
  );
};
