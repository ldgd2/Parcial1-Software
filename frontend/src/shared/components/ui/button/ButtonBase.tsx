import React from 'react';
import './button.css';

export interface ButtonBaseProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  isLoading?: boolean;
}

export const ButtonBase: React.FC<ButtonBaseProps> = ({
  variant = 'primary',
  isLoading,
  className = '',
  children,
  disabled,
  ...props
}) => {
  return (
    <button
      className={`widget-btn widget-btn-${variant} ${className}`}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading ? <span className="widget-btn-spinner" /> : null}
      {children}
    </button>
  );
};
