import React from 'react';
import { ButtonBase, type ButtonBaseProps } from './ButtonBase';

export const ButtonGhost: React.FC<Omit<ButtonBaseProps, 'variant'>> = (props) => {
  return <ButtonBase variant="ghost" {...props} />;
};
