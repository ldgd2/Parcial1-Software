import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginView } from '../features/gestion_usuarios/iniciar_sesion';
import { RegisterView } from '../features/gestion_usuarios/registrar_usuario';
import { ResetPasswordView } from '../features/gestion_usuarios/recuperar_password';
import { LandingView } from '../features/landing';
import { DashboardView } from '../features/gestion_proyectos/administrar_proyecto/views/DashboardView';
import { SalaView } from '../features/gestion_salas/entrar_sala/views/SalaView';
import { UnirseView } from '../features/gestion_salas/entrar_sala/views/UnirseView';

export const AppRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingView />} />
        <Route path="/login" element={<LoginView />} />
        <Route path="/register" element={<RegisterView />} />
        <Route path="/reset-password" element={<ResetPasswordView />} />
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/diagrama/:id" element={<SalaView />} />
        <Route path="/unirse/:codigo" element={<UnirseView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
