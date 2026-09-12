import React from 'react';
import './NuevoProyectoCard.css';

interface Props {
  onClick: () => void;
}

export const NuevoProyectoCard: React.FC<Props> = ({ onClick }) => (
  <button className="nuevo-proyecto-card" onClick={onClick} id="btn-nuevo-proyecto">
    <div className="nuevo-proyecto-card__plus">+</div>
    <span className="nuevo-proyecto-card__label">NUEVO PROYECTO</span>
  </button>
);
