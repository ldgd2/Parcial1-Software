import React from 'react';
import './shapes.css';

export interface ShapeBaseProps extends React.SVGAttributes<SVGSVGElement> {
  animation?: 'spin' | 'float' | 'pulse' | 'none';
  color?: string;
  size?: number;
}

export const ShapeBase: React.FC<{ children: React.ReactNode; className?: string } & ShapeBaseProps> = ({ 
  children, 
  animation = 'none', 
  className = '', 
  ...props 
}) => {
  return (
    <svg 
      className={`widget-shape shape-anim-${animation} ${className}`} 
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      {children}
    </svg>
  );
};
