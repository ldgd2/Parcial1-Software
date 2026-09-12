import React from 'react';
import { ShapeBase, type ShapeBaseProps } from './ShapeBase';

export const DotsPatternShape: React.FC<Omit<ShapeBaseProps, 'children'>> = ({ 
  size = 100, 
  color = 'var(--text-primary)', 
  ...props 
}) => {
  return (
    <ShapeBase width={size} height={size} viewBox="0 0 100 100" {...props}>
      <defs>
        <pattern id="dots" patternUnits="userSpaceOnUse" width="20" height="20">
          <circle cx="10" cy="10" r="4" fill={color} />
        </pattern>
      </defs>
      <rect width="100" height="100" fill="url(#dots)" />
    </ShapeBase>
  );
};
