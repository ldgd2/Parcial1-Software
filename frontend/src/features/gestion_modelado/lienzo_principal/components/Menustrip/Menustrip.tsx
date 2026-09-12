import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_URL } from '@/shared/lib/api';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { useSalaSocket } from '@/features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext';
import { PermisosModal } from '../PermisosModal/PermisosModal';
import type { SalaInfo } from '@/features/gestion_modelado/shared/types/types';
import './Menustrip.css';

interface Props {
  sala: SalaInfo;
  onSave: () => Promise<void>;
  saving: boolean;
}

interface MenuItem {
  label: string;
  items: { label?: string; shortcut?: string; action: () => void; separator?: boolean }[];
}

export const Menustrip: React.FC<Props> = ({ sala, onSave, saving }) => {
  const navigate = useNavigate();
  const { addNode, nodes, loadDiagram, getDiagramState } = useDiagram();
  const { pendingGuests } = useSalaSocket();
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [showShare, setShowShare] = useState(false);
  const [showPermisos, setShowPermisos] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const shareLink = `${window.location.origin}/unirse/${sala.codigo_acceso}`;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenu(null);
        setShowShare(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Ctrl+S
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        onSave();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onSave]);

  const copiarLink = async () => {
    await navigator.clipboard.writeText(shareLink);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  const exportarJSON = () => {
    const state = getDiagramState();
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sala.proyecto_nombre.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setOpenMenu(null);
  };

  const limpiarLienzo = () => {
    loadDiagram({ nodes: [], relations: [], version: 0 });
    setOpenMenu(null);
  };

  const exportarEA = async () => {
    try {
      await onSave();
      
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const response = await fetch(`${API_URL}/interoperabilidad/${sala.proyecto_id}/exportar-ea`, { headers });
      if (!response.ok) throw new Error('Error al exportar');
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `EA_${sala.proyecto_nombre.replace(/\s+/g, '_')}.xml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("No se pudo exportar a Enterprise Architect");
    }
    setOpenMenu(null);
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const importarEA = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const response = await fetch(`${API_URL}/interoperabilidad/${sala.proyecto_id}/importar-ea`, {
        method: 'POST',
        headers,
        body: formData
      });
      
      if (!response.ok) throw new Error('Error al importar');
      const result = await response.json();
      
      if (result.status === 'success') {
        loadDiagram({
          nodes: result.data.nodes,
          relations: result.data.relations,
          version: Date.now()
        });
      }
    } catch (e) {
      alert("Error importando desde XML");
    }
    
    setOpenMenu(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const menus: MenuItem[] = [
    {
      label: 'ARCHIVO',
      items: [
        { label: 'Guardar', shortcut: 'Ctrl+S', action: () => { onSave(); setOpenMenu(null); } },
        { label: 'Exportar JSON', action: exportarJSON },
        { separator: true, action: () => {} },
        { label: 'Importar desde EA (XML)', action: () => fileInputRef.current?.click() },
        { label: 'Exportar a EA (XML)', action: exportarEA },
        { label: 'Volver al Dashboard', action: () => navigate('/dashboard'), separator: true },
      ]
    },
    {
      label: 'INSERTAR',
      items: [
        { label: 'Nueva Clase', shortcut: 'Ctrl+Shift+C', action: () => { addNode(); setOpenMenu(null); } },
      ]
    },
    {
      label: 'EDICIÓN',
      items: [
        { label: 'Limpiar lienzo', action: limpiarLienzo },
      ]
    },
    {
      label: 'VER',
      items: [
        { label: 'Zoom: Ctrl + Rueda', action: () => setOpenMenu(null) },
        { label: 'Pan: Rueda del ratón', action: () => setOpenMenu(null) },
      ]
    },
    {
      label: 'HERRAMIENTAS',
      items: [
        { label: 'Permisos de Acceso', action: () => { setShowPermisos(true); setOpenMenu(null); } },
      ]
    }
  ];

  return (
    <>
    <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".xml" onChange={importarEA} />
    <div className="menustrip" ref={menuRef}>
      {/* App brand */}
      <div className="menustrip__brand">
        <span className="menustrip__brand-icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
        <span className="menustrip__project-name">{sala.proyecto_nombre}</span>
      </div>

      {/* Menu items */}
      <div className="menustrip__menus">
        {menus.map(menu => (
          <div key={menu.label} className="menustrip__menu-wrap">
            <button
              className={`menustrip__menu-btn ${openMenu === menu.label ? 'menustrip__menu-btn--active' : ''}`}
              onClick={() => setOpenMenu(openMenu === menu.label ? null : menu.label)}
              onMouseEnter={() => openMenu ? setOpenMenu(menu.label) : undefined}
            >
              {menu.label}
            </button>
            {openMenu === menu.label && (
              <div className="menustrip__dropdown">
                {menu.items.map((item, i) => (
                  <React.Fragment key={i}>
                    {item.separator && <div className="menustrip__dropdown-sep" />}
                    <button className="menustrip__dropdown-item" onClick={item.action}>
                      <span>{item.label}</span>
                      {item.shortcut && <span className="menustrip__shortcut">{item.shortcut}</span>}
                    </button>
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Right side */}
      <div className="menustrip__right">
        {pendingGuests.length > 0 && (
          <button 
            className="menustrip__notification-badge"
            onClick={() => setShowPermisos(true)}
            title="Solicitudes de acceso"
          >
            {pendingGuests.length} en espera
          </button>
        )}
        <span className="menustrip__node-count">{nodes.length} clases</span>

        {/* Save indicator */}
        <button
          className={`menustrip__save-btn ${saving ? 'menustrip__save-btn--saving' : ''}`}
          onClick={onSave}
          disabled={saving}
          id="btn-guardar-lienzo"
        >
          {saving ? 'GUARDANDO...' : 'GUARDAR'}
        </button>

        {/* Share */}
        <div className="menustrip__share-wrap">
          <button
            className="menustrip__share-btn"
            onClick={() => setShowShare(v => !v)}
            id="btn-compartir-sala"
          >
            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg> COMPARTIR
          </button>
          {showShare && (
            <div className="menustrip__share-panel">
              <div className="menustrip__share-label">ENLACE DE INVITACIÓN</div>
              <div className="menustrip__share-row">
                <input
                  id="input-share-link"
                  className="menustrip__share-input"
                  value={shareLink}
                  readOnly
                  onClick={e => (e.target as HTMLInputElement).select()}
                />
                <button
                  id="btn-copiar-enlace"
                  className={`menustrip__share-copy ${copiado ? 'menustrip__share-copy--done' : ''}`}
                  onClick={copiarLink}
                >
                  {copiado ? <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polyline points="20 6 9 17 4 12"/></svg> COPIADO</> : 'COPIAR'}
                </button>
              </div>
              <p className="menustrip__share-hint">
                Cualquier persona con este enlace puede solicitar unirse al diagrama.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
    
    {showPermisos && (
      <PermisosModal 
        onClose={() => setShowPermisos(false)} 
        proyectoId={sala.proyecto_id}
      />
    )}
    </>
  );
};
