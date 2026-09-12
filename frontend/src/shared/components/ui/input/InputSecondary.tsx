import React from 'react';
import { InputBase, type InputBaseProps } from './InputBase';

export const InputSecondary: React.FC<Omit<InputBaseProps, 'variant'>> = (props) => {
  return <InputBase variant="secondary" {...props} />;
};
