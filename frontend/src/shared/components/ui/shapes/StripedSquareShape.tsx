import React from 'react';
import { ShapeBase, type ShapeBaseProps } from './ShapeBase';

export const StripedSquareShape: React.FC<Omit<ShapeBaseProps, 'children'>> = ({ 
  size = 100, 
  color = 'var(--text-primary)', 
  ...props 
}) => {
  return (
    <ShapeBase width={size} height={size} viewBox="0 0 100 100" {...props}>
      <defs>
        <pattern id="stripes" patternUnits="userSpaceOnUse" width="20" height="20" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="20" stroke={color} strokeWidth="10" />
        </pattern>
      </defs>
      <rect width="100" height="100" fill="url(#stripes)" />
    </ShapeBase>
  );
};
