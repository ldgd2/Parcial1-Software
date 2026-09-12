import React from 'react';
import { Widget } from '../../../shared/components/ui/Widget';

export const FeaturesSection: React.FC = () => {
  const features = [
    {
      title: 'Sincronización Total',
      description: 'Lienzo digital sin retrasos.',
    },
    {
      title: 'Generación IA',
      description: 'Convierte UML a código fuente.',
    },
    {
      title: 'Historial Visual',
      description: 'Control de versiones integrado.',
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
            <Widget.Card.Interactive className="feature-card-flat">
              <h3 className="feature-title-flat">0{idx + 1} // {feat.title}</h3>
              <p className="feature-desc-flat">{feat.description}</p>
            </Widget.Card.Interactive>
          </Widget.Animation.FadeIn>
        ))}
      </div>
    </section>
  );
};
