import React from 'react';
import { BadgeBase, type BadgeBaseProps } from './BadgeBase';

export const BadgePrimary: React.FC<Omit<BadgeBaseProps, 'variant'>> = (props) => {
  return <BadgeBase variant="primary" {...props} />;
};
