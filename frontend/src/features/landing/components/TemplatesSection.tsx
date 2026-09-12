import React from 'react';
import { Widget } from '../../../shared/components/ui/Widget';

export const TemplatesSection: React.FC = () => {
  const templates = ['E-Commerce', 'SaaS Auth', 'Microservicios', 'BBDD Relacional'];

  return (
    <section id="templates" className="landing-templates-minimal">
      <div className="section-header-flat">
        <h2 className="section-title-huge">PLANTILLAS<br/>LISTAS.</h2>
        <Widget.Shapes.DotsPattern size={100} color="var(--accent)" />
      </div>

      <div className="templates-grid-flat">
        {templates.map((tpl, idx) => (
          <Widget.Animation.FadeIn key={idx} delay={0.2 + idx * 0.1} direction="left">
            <div className="template-card-flat">
              <div className="tpl-box-flat" style={{ 
                background: idx % 2 === 0 ? 'var(--bg-color)' : 'var(--primary)',
                color: idx % 2 === 0 ? 'var(--text-primary)' : 'var(--bg-color)'
              }}>
                {idx + 1}
              </div>
              <p className="template-title-flat">{tpl}</p>
            </div>
          </Widget.Animation.FadeIn>
        ))}
      </div>
    </section>
  );
};
