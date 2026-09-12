import React, { useEffect, useRef } from 'react';
import { Widget } from '../../../shared/components/ui/Widget';

export const InteractiveBackground: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let animationFrameId: number;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      // Calculate mouse position relative to center of screen (-100 to 100)
      targetX = (e.clientX / window.innerWidth - 0.5) * 200;
      targetY = (e.clientY / window.innerHeight - 0.5) * 200;
    };

    const animate = () => {
      // Smooth interpolation
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      if (containerRef.current) {
        containerRef.current.style.setProperty('--mouse-x', `${currentX}`);
        containerRef.current.style.setProperty('--mouse-y', `${currentY}`);
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove);
    animate();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div ref={containerRef} className="interactive-background">
      {/* Layer 1: Slowest */}
      <div className="parallax-layer" style={{ '--parallax-factor': 0.1 } as any}>
        <Widget.Shapes.Circle size={400} color="var(--primary)" className="ib-shape" style={{ top: '-10%', left: '-10%', opacity: 0.1 }} />
        <Widget.Shapes.DotsPattern size={300} color="var(--secondary)" className="ib-shape" style={{ bottom: '-5%', right: '10%', opacity: 0.1 }} />
      </div>

      {/* Layer 2: Medium */}
      <div className="parallax-layer" style={{ '--parallax-factor': -0.2 } as any}>
        <Widget.Shapes.StripedSquare size={200} color="var(--accent)" className="ib-shape" style={{ top: '30%', right: '-5%', opacity: 0.15 }} />
        <Widget.Shapes.HalfCircle size={150} color="var(--border-color)" className="ib-shape" style={{ top: '60%', left: '5%', opacity: 0.2 }} />
      </div>

      {/* Layer 3: Fast */}
      <div className="parallax-layer" style={{ '--parallax-factor': 0.4 } as any}>
        <Widget.Shapes.Circle size={80} color="var(--accent)" className="ib-shape" style={{ top: '15%', left: '40%', opacity: 0.3 }} />
        <Widget.Shapes.StripedSquare size={120} color="var(--primary)" className="ib-shape" style={{ bottom: '20%', left: '30%', opacity: 0.2 }} />
        <Widget.Shapes.DotsPattern size={150} color="var(--text-secondary)" className="ib-shape" style={{ top: '50%', right: '25%', opacity: 0.1 }} />
      </div>
      
      {/* Layer 4: Floating Particles */}
      <div className="parallax-layer" style={{ '--parallax-factor': -0.5 } as any}>
        {[...Array(15)].map((_, i) => (
          <div 
            key={i} 
            className="ib-particle"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              width: `${Math.random() * 6 + 2}px`,
              height: `${Math.random() * 6 + 2}px`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${Math.random() * 10 + 10}s`
            }}
          />
        ))}
      </div>
    </div>
  );
};
