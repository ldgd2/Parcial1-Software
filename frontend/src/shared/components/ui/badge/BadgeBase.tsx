import React from 'react';
import './badge.css';

export interface BadgeBaseProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'outline';
  children: React.ReactNode;
}

export const BadgeBase: React.FC<BadgeBaseProps> = ({ 
  variant = 'primary', 
  children, 
  className = '', 
  ...props 
}) => {
  return (
    <span className={`widget-badge widget-badge-${variant} ${className}`} {...props}>
      {children}
    </span>
  );
};
