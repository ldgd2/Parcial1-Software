import React from 'react';
import { ButtonBase, type ButtonBaseProps } from './ButtonBase';

export const ButtonSecondary: React.FC<Omit<ButtonBaseProps, 'variant'>> = (props) => {
  return <ButtonBase variant="secondary" {...props} />;
};
