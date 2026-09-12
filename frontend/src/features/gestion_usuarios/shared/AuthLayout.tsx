import React from 'react';
import { Widget } from '../../../shared/components/ui/Widget';
import './auth.css';

interface AuthLayoutProps {
  children: React.ReactNode;
  backgroundShapes?: React.ReactNode;
  title: string;
  subtitle: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, backgroundShapes, title, subtitle }) => {
  return (
    <div className="auth-layout">
      {/* Default floating particles for fluidity */}
      <div className="auth-particles">
        {[...Array(10)].map((_, i) => (
          <div 
            key={i} 
            className="ib-particle"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              width: `${Math.random() * 4 + 2}px`,
              height: `${Math.random() * 4 + 2}px`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${Math.random() * 15 + 10}s`
            }}
          />
        ))}
      </div>

      {/* Dynamic Background specific to the view */}
      <div className="auth-background">
        {backgroundShapes}
      </div>
      
      {/* Content wrapper */}
      <div className="auth-content-wrapper">
        <Widget.Animation.FadeIn delay={0.1} direction="up">
          <div className="auth-card-flat">
            <div className="auth-header-flat">
              <div className="flat-dots">
                <span></span><span></span><span></span>
              </div>
              <div className="flat-title">PORTAL DE ACCESO</div>
            </div>
            
            <div className="auth-body">
              <h1 className="auth-title-huge">{title}</h1>
              <p className="auth-subtitle">{subtitle}</p>
              
              <div className="auth-form-container">
                {children}
              </div>
            </div>
          </div>
        </Widget.Animation.FadeIn>
      </div>
    </div>
  );
};
