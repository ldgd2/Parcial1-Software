import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../shared/components/ui/Widget';

export const HeroSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section className="landing-hero-minimal">
      {/* Left Side - Typography & CTAs */}
      <div className="hero-left">
        <Widget.Animation.FadeIn delay={0.1} direction="up">
          <div className="hero-badge-minimal">SISTEMA v2.0</div>
        </Widget.Animation.FadeIn>
        
        <Widget.Animation.FadeIn delay={0.2} direction="up">
          <h1 className="hero-title-massive">
            DISEÑO /<br/>
            ARQUITECTURA
          </h1>
        </Widget.Animation.FadeIn>

        <Widget.Animation.FadeIn delay={0.3} direction="up">
          <p className="hero-desc-minimal">
            Una herramienta pura y sin distracciones para ingenieros de software. Construye de forma colaborativa.
          </p>
        </Widget.Animation.FadeIn>

        <Widget.Animation.FadeIn delay={0.4} direction="up">
          <div className="hero-actions-minimal">
            <Widget.Button.Primary onClick={() => navigate('/login')}>
              EMPEZAR AHORA
            </Widget.Button.Primary>
            <Widget.Button.Ghost onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>
              SABER MÁS
            </Widget.Button.Ghost>
          </div>
        </Widget.Animation.FadeIn>
      </div>

      {/* Right Side - Flat Mockup & Shapes */}
      <div className="hero-right">
        {/* Animated Background Shapes */}
        <div className="shapes-container">
           <Widget.Shapes.Circle size={150} color="var(--accent)" animation="float" className="shape-1" />
           <Widget.Shapes.StripedSquare size={120} color="var(--primary)" animation="spin" className="shape-2" />
           <Widget.Shapes.DotsPattern size={200} color="var(--secondary)" className="shape-3" />
        </div>

        <Widget.Animation.FadeIn delay={0.5} direction="left">
          {/* Flat Minimalist UML Mockup */}
          <div className="flat-mockup-window">
            <div className="flat-mockup-header">
              <div className="flat-dots">
                <span></span><span></span><span></span>
              </div>
              <div className="flat-title">architecture.sys</div>
            </div>
            <div className="flat-mockup-body">
              {/* Box 1 */}
              <div className="flat-node" style={{ top: '10%', left: '10%' }}>
                <div className="node-head">User</div>
                <div className="node-body">
                  id: uuid<br/>email: string
                </div>
              </div>
              {/* Line */}
              <div className="flat-line" style={{ top: '30%', left: '40%', width: '60px' }}></div>
              {/* Box 2 */}
              <div className="flat-node outline" style={{ top: '25%', left: '55%' }}>
                <div className="node-head outline-head">Session</div>
                <div className="node-body">
                  token: string<br/>valid: bool
                </div>
              </div>
            </div>
          </div>
        </Widget.Animation.FadeIn>
      </div>
    </section>
  );
};
