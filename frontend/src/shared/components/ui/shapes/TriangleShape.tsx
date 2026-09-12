import React from 'react';
import { ShapeBase, type ShapeBaseProps } from './ShapeBase';

export const TriangleShape: React.FC<ShapeBaseProps> = (props) => (
  <ShapeBase viewBox="0 0 100 100" {...props}>
    <polygon points="50,10 90,90 10,90" fill="currentColor" />
  </ShapeBase>
);
