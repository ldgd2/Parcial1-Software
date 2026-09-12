import React from 'react';
import { ShapeBase, type ShapeBaseProps } from './ShapeBase';

export const HalfCircleShape: React.FC<Omit<ShapeBaseProps, 'children'>> = ({ 
  size = 100, 
  color = 'var(--text-primary)', 
  ...props 
}) => {
  return (
    <ShapeBase width={size} height={size} viewBox="0 0 100 100" {...props}>
      <path d="M 10 50 A 40 40 0 0 1 90 50 Z" fill={color} />
    </ShapeBase>
  );
};
