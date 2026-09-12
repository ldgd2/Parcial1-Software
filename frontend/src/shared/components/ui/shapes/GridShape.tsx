import React from 'react';
import { ShapeBase, type ShapeBaseProps } from './ShapeBase';

export const GridShape: React.FC<ShapeBaseProps> = (props) => (
  <ShapeBase viewBox="0 0 100 100" {...props}>
    <pattern id="gridPattern" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeWidth="2" />
    </pattern>
    <rect width="100" height="100" fill="url(#gridPattern)" />
  </ShapeBase>
);
