import React, { useRef, useEffect } from 'react';
import './DashboardBackground.css';

export const DashboardBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    const resize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resize);

    // Floating particles
    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.4 + 0.05,
    }));

    // Grid lines
    const gridSpacing = 80;

    let t = 0;
    const draw = () => {
      t += 0.005;
      ctx.clearRect(0, 0, width, height);

      // Draw animated grid
      ctx.strokeStyle = 'rgba(223, 208, 184, 0.04)';
      ctx.lineWidth = 1;
      const offsetX = (t * 10) % gridSpacing;
      const offsetY = (t * 8) % gridSpacing;
      for (let x = -gridSpacing + offsetX; x < width + gridSpacing; x += gridSpacing) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
      }
      for (let y = -gridSpacing + offsetY; y < height + gridSpacing; y += gridSpacing) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
      }

      // Floating particles
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(223, 208, 184, ${p.alpha})`;
        ctx.fill();
      });

      // Slow pulsing circles
      const pulse1 = Math.sin(t * 0.8) * 0.03 + 0.04;
      ctx.beginPath();
      ctx.arc(width * 0.15, height * 0.2, 300, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(223, 208, 184, ${pulse1})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      const pulse2 = Math.sin(t * 0.5 + 1) * 0.02 + 0.03;
      ctx.beginPath();
      ctx.arc(width * 0.88, height * 0.75, 250, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(148, 137, 121, ${pulse2})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return <canvas ref={canvasRef} className="dashboard-bg-canvas" />;
};
