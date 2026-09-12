import React from 'react';
import { ShapeBase, type ShapeBaseProps } from './ShapeBase';

export const CircleShape: React.FC<Omit<ShapeBaseProps, 'children'> & { filled?: boolean }> = ({ 
  size = 100, 
  color = 'var(--text-primary)', 
  filled = true,
  ...props 
}) => {
  return (
    <ShapeBase width={size} height={size} viewBox="0 0 100 100" {...props}>
      <circle 
        cx="50" cy="50" r="45" 
        fill={filled ? color : 'none'} 
        stroke={filled ? 'none' : color} 
        strokeWidth={filled ? 0 : 10} 
      />
    </ShapeBase>
  );
};
