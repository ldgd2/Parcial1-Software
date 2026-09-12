import React from 'react';
import { CardBase, type CardBaseProps } from './CardBase';

export const CardInteractive: React.FC<Omit<CardBaseProps, 'variant'>> = (props) => {
  return <CardBase variant="interactive" {...props} />;
};
