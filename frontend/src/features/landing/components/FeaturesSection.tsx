import React from 'react';
import { Widget } from '../../../shared/components/ui/Widget';

export const FeaturesSection: React.FC = () => {
  const features = [
    {
      title: 'Modelado UML',
      description: 'Crea diagramas de clases, interfaces, enums y relaciones con una interfaz fluida e intuitiva.',
    },
    {
      title: 'Inteligencia Artificial',
      description: 'Envía tus requerimientos y la IA estructurará y conectará los elementos del diagrama por ti.',
    },
    {
      title: 'Colaboración en Tiempo Real',
      description: 'Trabaja en equipo. Ve los cursores de tus compañeros y los cambios instantáneos.',
    },
    {
      title: 'Control de Versiones y Offline',
      description: 'Trabaja sin conexión y el sistema hará merge automático de los conflictos al reconectar.',
    }
  ];

  return (
    <section id="features" className="landing-features-minimal">
      <div className="features-header-split">
        <Widget.Animation.FadeIn delay={0.1} direction="up">
          <h2 className="section-title-huge">TODO LO<br/>QUE NECESITAS.</h2>
        </Widget.Animation.FadeIn>
        
        <Widget.Animation.FadeIn delay={0.2} direction="up">
           <Widget.Shapes.HalfCircle size={80} color="var(--primary)" animation="float" />
        </Widget.Animation.FadeIn>
      </div>

      <div className="features-grid-minimal">
        {features.map((feat, idx) => (
          <Widget.Animation.FadeIn key={idx} delay={0.3 + idx * 0.1} direction="up">
            <Widget.Card.Interactive className="feature-card-fluid">
              <h3 className="feature-title-fluid">0{idx + 1} // {feat.title}</h3>
              <p className="feature-desc-fluid">{feat.description}</p>
            </Widget.Card.Interactive>
          </Widget.Animation.FadeIn>
        ))}
      </div>
    </section>
  );
};

