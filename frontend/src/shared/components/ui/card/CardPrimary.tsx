import React from 'react';
import { CardBase, type CardBaseProps } from './CardBase';

export const CardPrimary: React.FC<Omit<CardBaseProps, 'variant'>> = (props) => {
  return <CardBase variant="primary" {...props} />;
};
