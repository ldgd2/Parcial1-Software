import React from 'react';
import { useNavigate } from 'react-router-dom';
import { TokenService } from '@/shared/lib/TokenService';
import './DashboardNavbar.css';

interface Props {
  userName: string;
}

export const DashboardNavbar: React.FC<Props> = ({ userName }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    TokenService.removeToken();
    navigate('/login');
  };

  const initials = userName
    .split(' ')
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase();

  return (
    <nav className="dash-navbar">
      <div className="dash-navbar__brand">
        <span className="dash-navbar__logo"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
        <span className="dash-navbar__name">DIAGRAMADOR</span>
      </div>
      <div className="dash-navbar__right">
        <div className="dash-navbar__user">
          <div className="dash-navbar__avatar">{initials}</div>
          <span className="dash-navbar__username">{userName}</span>
        </div>
        <button className="dash-navbar__logout" onClick={handleLogout}>
          SALIR
        </button>
      </div>
    </nav>
  );
};
