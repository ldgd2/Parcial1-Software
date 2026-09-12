import React from 'react';
import { BadgeBase, type BadgeBaseProps } from './BadgeBase';

export const BadgeOutline: React.FC<Omit<BadgeBaseProps, 'variant'>> = (props) => {
  return <BadgeBase variant="outline" {...props} />;
};
