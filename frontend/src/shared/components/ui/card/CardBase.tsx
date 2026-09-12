import React from 'react';
import './card.css';

export interface CardBaseProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'primary' | 'interactive';
  children: React.ReactNode;
}

export const CardBase: React.FC<CardBaseProps> = ({ 
  variant = 'primary', 
  children, 
  className = '', 
  ...props 
}) => {
  return (
    <div className={`widget-card widget-card-${variant} ${className}`} {...props}>
      {children}
    </div>
  );
};
