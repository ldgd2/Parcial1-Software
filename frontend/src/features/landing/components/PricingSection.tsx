import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../shared/components/ui/Widget';

export const PricingSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section id="pricing" className="landing-pricing-minimal">
      <div className="pricing-split">
        <div className="pricing-left">
          <Widget.Animation.FadeIn delay={0.1} direction="up">
            <h2 className="section-title-huge text-dark">ACCESO<br/>LIBRE.</h2>
            <p className="pricing-desc-flat">Sin costes ocultos. Sin sorpresas. Todo el poder de la arquitectura a tu disposición.</p>
          </Widget.Animation.FadeIn>
        </div>
        
        <div className="pricing-right">
          <Widget.Animation.FadeIn delay={0.3} direction="up">
            <div className="pricing-card-flat">
              <h3 className="pricing-tier-flat">GRATIS</h3>
              <div className="pricing-price-flat">0€</div>
              <ul className="pricing-features-flat">
                <li>Diagramas Ilimitados</li>
                <li>Colaboración en Tiempo Real</li>
                <li>Exportación PNG/PDF</li>
              </ul>
              <Widget.Button.Primary onClick={() => navigate('/login')} className="btn-massive">
                CREAR CUENTA
              </Widget.Button.Primary>
            </div>
          </Widget.Animation.FadeIn>
        </div>
      </div>
    </section>
  );
};
