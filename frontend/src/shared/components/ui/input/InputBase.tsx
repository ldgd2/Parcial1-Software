import React from 'react';
import './input.css';

export interface InputBaseProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'primary' | 'secondary';
  label?: string;
  error?: string;
}

export const InputBase: React.FC<InputBaseProps> = ({ 
  variant = 'primary', 
  label, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
    <div className={`widget-input-wrapper ${className}`}>
      {label && <label className="widget-input-label">{label}</label>}
      <input 
        className={`widget-input widget-input-${variant} ${error ? 'widget-input-error' : ''}`}
        {...props} 
      />
      {error && <span className="widget-input-error-msg">{error}</span>}
    </div>
  );
};
