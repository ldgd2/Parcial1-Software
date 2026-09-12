import React from 'react';
import { Layers, Globe, Mail, MessageSquare } from 'lucide-react';
import './layout.css';

export const Footer: React.FC = () => {
  return (
    <footer className="widget-footer">
      <div className="footer-container">
        <div className="footer-brand">
          <div className="footer-logo">
            <Layers size={24} className="text-primary" />
            <span className="font-bold">SysUML</span>
          </div>
          <p className="footer-desc">
            Diseña la arquitectura de tu software de forma colaborativa, ágil y visual.
          </p>
        </div>
        
        <div className="footer-links-grid">
          <div className="footer-column">
            <h4>Producto</h4>
            <a href="#">Precios</a>
            <a href="#">Características</a>
            <a href="#">Plantillas</a>
          </div>
          <div className="footer-column">
            <h4>Compañía</h4>
            <a href="#">Acerca de</a>
            <a href="#">Blog</a>
            <a href="#">Soporte</a>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>© 2026 SysUML Inc. Todos los derechos reservados.</p>
        <div className="footer-social">
          <Globe size={18} />
          <Mail size={18} />
          <MessageSquare size={18} />
        </div>
      </div>
    </footer>
  );
};
