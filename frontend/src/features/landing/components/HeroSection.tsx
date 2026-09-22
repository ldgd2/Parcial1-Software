import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Widget } from '../../../shared/components/ui/Widget';
import { ClassNode } from '@/features/gestion_modelado/editar_elemento/components/ClassNode/ClassNode';
import { DiagramProvider, useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { RealTimeSyncProvider } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import type { ClassNode as ClassNodeType } from '@/features/gestion_modelado/shared/types/types';

const mockNodes: ClassNodeType[] = [
  {
    id: 'hero_node_1',
    type: 'class',
    x: 0,
    y: 0,
    width: 220,
    nombre: 'Usuario',
    color: '#ed8936',
    version: 0,
    hash: '',
    atributos: [
      { id: 'a1', nombre: 'id', tipo: 'UUID', visibilidad: '+', version: 0 },
      { id: 'a2', nombre: 'email', tipo: 'String', visibilidad: '+', version: 0 }
    ],
    metodos: []
  },
  {
    id: 'hero_node_2',
    type: 'class',
    x: 250,
    y: 80,
    width: 220,
    nombre: 'Proyecto',
    color: '#ed8936',
    version: 0,
    hash: '',
    atributos: [
      { id: 'b1', nombre: 'nombre', tipo: 'String', visibilidad: '+', version: 0 },
      { id: 'b2', nombre: 'ownerId', tipo: 'UUID', visibilidad: '+', version: 0 }
    ],
    metodos: []
  }
];

const MockupCanvas = () => {
  const { loadDiagram } = useDiagram();

  useEffect(() => {
    loadDiagram({ nodes: mockNodes, relations: [], version: 1, correcciones: {} });
  }, [loadDiagram]);

  return (
    <div className="fluid-mockup-body" style={{ position: 'relative', width: '100%', height: '100%', transform: 'scale(0.7)', transformOrigin: 'top left' }}>
      <div style={{ position: 'absolute', top: '10%', left: '5%' }}>
        <ClassNode node={mockNodes[0]} onDragStart={() => {}} />
      </div>
      <svg className="fluid-relation" style={{ top: '35%', left: '42%', width: '100px', height: '2px', position: 'absolute' }}>
          <line x1="0" y1="1" x2="100" y2="1" stroke="var(--primary)" strokeWidth="2" strokeDasharray="5,5" />
      </svg>
      <div style={{ position: 'absolute', top: '30%', left: '45%' }}>
        <ClassNode node={mockNodes[1]} onDragStart={() => {}} />
      </div>
      <div className="ai-voice-indicator" style={{ position: 'absolute', bottom: '10%', left: '30%' }}>
          <div className="pulse-ring"></div>
          <span>"Generar relación de 1 a muchos"</span>
      </div>
    </div>
  );
};

export const HeroSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section className="landing-hero-minimal">
      {/* Left Side - Typography & CTAs */}
      <div className="hero-left">
        <Widget.Animation.FadeIn delay={0.1} direction="up">
          <h1 className="hero-title-massive">
            MODELADO UML<br/>
            INTELIGENTE
          </h1>
        </Widget.Animation.FadeIn>

        <Widget.Animation.FadeIn delay={0.2} direction="up">
          <p className="hero-desc-minimal">
            El diagrama perfecto a la velocidad de tu voz. Diseña sistemas de software complejos de forma colaborativa, con la asistencia de Inteligencia Artificial y control de versiones offline integrado.
          </p>
        </Widget.Animation.FadeIn>

        <Widget.Animation.FadeIn delay={0.3} direction="up">
          <div className="hero-actions-minimal">
            <Widget.Button.Primary onClick={() => navigate('/login')}>
              COMENZAR AHORA
            </Widget.Button.Primary>
            <Widget.Button.Ghost onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>
              VER CARACTERÍSTICAS
            </Widget.Button.Ghost>
          </div>
        </Widget.Animation.FadeIn>
      </div>

      {/* Right Side - Fluid Mockup & Shapes */}
      <div className="hero-right">
        {/* Animated Background Shapes */}
        <div className="shapes-container">
           <Widget.Shapes.Circle size={200} color="var(--primary)" animation="float" className="shape-1" />
           <Widget.Shapes.Circle size={150} color="var(--secondary)" animation="spin" className="shape-2" />
           <Widget.Shapes.DotsPattern size={250} color="var(--accent)" className="shape-3" />
        </div>

        <Widget.Animation.FadeIn delay={0.4} direction="left">
          {/* Fluid Minimalist UML Mockup */}
          <div className="fluid-mockup-window">
            <RealTimeSyncProvider sala={{ isOfflineMode: true, codigo_acceso: 'demo' }}>
              <DiagramProvider>
                <MockupCanvas />
              </DiagramProvider>
            </RealTimeSyncProvider>
          </div>
        </Widget.Animation.FadeIn>
      </div>
    </section>
  );
};

