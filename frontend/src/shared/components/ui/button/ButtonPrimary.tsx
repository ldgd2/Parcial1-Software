import React from 'react';
import { ButtonBase, type ButtonBaseProps } from './ButtonBase';

export const ButtonPrimary: React.FC<Omit<ButtonBaseProps, 'variant'>> = (props) => {
  return <ButtonBase variant="primary" {...props} />;
};
