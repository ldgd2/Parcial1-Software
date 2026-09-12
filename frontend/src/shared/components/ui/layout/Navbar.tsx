import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../Widget';
import { Layers } from 'lucide-react';
import './layout.css';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();

  return (
    <nav className="widget-navbar">
      <div className="navbar-container">
        <div className="navbar-logo" onClick={() => navigate('/')}>
          <Layers size={24} className="text-primary" />
          <span className="font-bold">SysUML</span>
        </div>
        
        <div className="navbar-links">
          <a href="#features">Características</a>
          <a href="#templates">Plantillas</a>
          <a href="#pricing">Precios</a>
        </div>

        <div className="navbar-actions">
          <Widget.Button.Ghost onClick={() => navigate('/login')}>
            Iniciar Sesión
          </Widget.Button.Ghost>
          <Widget.Button.Primary onClick={() => navigate('/login')}>
            Pruébalo Gratis
          </Widget.Button.Primary>
        </div>
      </div>
    </nav>
  );
};
