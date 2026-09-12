import React from 'react';
import { InputBase, type InputBaseProps } from './InputBase';

export const InputPrimary: React.FC<Omit<InputBaseProps, 'variant'>> = (props) => {
  return <InputBase variant="primary" {...props} />;
};
