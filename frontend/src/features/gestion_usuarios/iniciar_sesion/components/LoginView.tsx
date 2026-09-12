import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../../shared/components/ui/Widget';
import { AuthLayout } from '../../shared/AuthLayout';
import { apiFetch } from '../../../../shared/lib/api';

export const LoginView: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    try {
      const data = await apiFetch('/usuarios/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        
        try {
          const user = await apiFetch('/usuarios/me');
          if (user && user.nombre) {
            localStorage.setItem('usuario_nombre', user.nombre);
          }
        } catch (e) {
          // ignore
        }
        
        navigate('/dashboard');
      }
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const loginBackground = (
    <div style={{ position: 'absolute', width: '100%', height: '100%' }}>
      <Widget.Shapes.Circle size={300} color="var(--primary)" animation="float" style={{ position: 'absolute', top: '10%', right: '10%', opacity: 0.15 }} />
      <Widget.Shapes.StripedSquare size={200} color="var(--accent)" animation="spin" style={{ position: 'absolute', bottom: '10%', left: '5%', opacity: 0.2 }} />
      <Widget.Shapes.DotsPattern size={250} color="var(--text-secondary)" style={{ position: 'absolute', top: '40%', left: '20%', opacity: 0.1 }} />
      <Widget.Shapes.Triangle size={150} color="var(--secondary)" animation="pulse" style={{ position: 'absolute', top: '70%', right: '20%', opacity: 0.2 }} />
      <Widget.Shapes.Grid size={200} color="var(--border-color)" animation="float" style={{ position: 'absolute', top: '-5%', left: '30%', opacity: 0.3 }} />
    </div>
  );

  return (
    <AuthLayout 
      title="ACCEDER" 
      subtitle="Ingresa tus credenciales para continuar al sistema."
      backgroundShapes={loginBackground}
    >
      <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {errorMsg && <div style={{ color: 'var(--accent)', fontSize: '0.9rem', textAlign: 'center' }}>{errorMsg}</div>}
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
            ENTRAR
          </Widget.Button.Primary>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
            <Widget.Button.Ghost type="button" onClick={() => navigate('/reset-password')}>
              ¿Olvidaste tu contraseña?
            </Widget.Button.Ghost>
            <Widget.Button.Ghost type="button" onClick={() => navigate('/register')}>
              Crear cuenta
            </Widget.Button.Ghost>
          </div>
        </div>
      </form>
    </AuthLayout>
  );
};
