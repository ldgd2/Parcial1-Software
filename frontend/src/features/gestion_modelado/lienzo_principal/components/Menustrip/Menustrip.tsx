import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { useRealTimeSync } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { PermisosModal } from '../PermisosModal/PermisosModal';
import { SettingsModal } from '@/features/gestion_proyectos/administrar_proyecto/components/SettingsModal/SettingsModal';
import { ExportModal } from '@/features/gestion_asistencia_ia/exportar_github/components/ExportModal/ExportModal';
import { TokenService } from '@/shared/lib/TokenService';
import { API_URL } from '@/shared/lib/api';
import type { SalaInfo } from '@/features/gestion_modelado/shared/types/types';
import { XmiExporter } from '@/features/gestion_interoperabilidad_frontend/utils/xmi/core/XmiExporter';
import { XmiImporter } from '@/features/gestion_interoperabilidad_frontend/utils/xmi/core/XmiImporter';
import { useExportarGithub } from '@/features/gestion_asistencia_ia/exportar_github/hooks/useExportarGithub';
import './Menustrip.css';

interface Props {
  sala: SalaInfo;
  onSave: () => Promise<void>;
  saving: boolean;
  onOpenChat: () => void;
}

interface MenuItem {
  label: string;
  items: { label?: string; shortcut?: string; action: () => void; separator?: boolean }[];
}

export const Menustrip: React.FC<Props> = ({ sala, onSave, saving, onOpenChat }) => {
  const navigate = useNavigate();
  const { addNode, nodes, loadDiagram, getDiagramState } = useDiagram();
  const { pendingGuests } = useRealTimeSync();
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [showShare, setShowShare] = useState(false);
  const [showPermisos, setShowPermisos] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  const { githubUsername, isExporting, isLoadingStatus } = useExportarGithub();

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
      
      const isOffline = !navigator.onLine;

      if (!isOffline) {
        try {
          const token = TokenService.getToken();
          const headers: Record<string, string> = {};
          if (token) headers['Authorization'] = `Bearer ${token}`;
          
          const response = await fetch(`${API_URL}/interoperabilidad/${sala.proyecto_id}/exportar-ea`, { headers });
          if (!response.ok) throw new Error('Error backend');
          
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `EA_${sala.proyecto_nombre.replace(/\s+/g, '_')}.xml`;
          a.click();
          URL.revokeObjectURL(url);
          setOpenMenu(null);
          return;
        } catch (e) {
          console.warn("Backend export failed, falling back to frontend export");
        }
      }

      // Fallback/Offline export
      const exporter = new XmiExporter();
      const xmlString = exporter.export(getDiagramState(), sala.proyecto_nombre);
      const blob = new Blob([xmlString], { type: 'application/xml' });
      
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
  const jsonFileInputRef = useRef<HTMLInputElement>(null);

  const importarEA = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const isOffline = !navigator.onLine;
      
      if (!isOffline) {
        try {
          const formData = new FormData();
          formData.append('file', file);
          
          const token = TokenService.getToken();
          const headers: Record<string, string> = {};
          if (token) headers['Authorization'] = `Bearer ${token}`;
          
          const response = await fetch(`${API_URL}/interoperabilidad/${sala.proyecto_id}/importar-ea`, {
            method: 'POST',
            headers,
            body: formData
          });
          
          if (!response.ok) throw new Error('Error backend');
          const result = await response.json();
          
          if (result.status === 'success') {
            loadDiagram({
              nodes: result.data.nodes,
              relations: result.data.relations,
              version: Date.now()
            });
            setOpenMenu(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
            return;
          }
        } catch (err) {
          console.warn("Backend import failed, falling back to frontend import");
        }
      }

      // Fallback/Offline import
      const text = await file.text();
      const importer = new XmiImporter();
      const state = importer.import(text);
      loadDiagram(state);
    } catch (e) {
      alert("Error importando desde XML");
    }
    
    setOpenMenu(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const importarJSON = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const state = JSON.parse(text);
      loadDiagram(state);
    } catch (e) {
      alert("Error importando JSON");
    }
    
    setOpenMenu(null);
    if (jsonFileInputRef.current) jsonFileInputRef.current.value = '';
  };

  const [notification, setNotification] = useState<{type: 'success' | 'error', message: string} | null>(null);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const openExportModal = () => {
    if (!githubUsername) {
      showNotification('error', "Por favor vincula tu cuenta de GitHub primero desde la Configuración.");
      setShowSettings(true);
      return;
    }
    setShowExportModal(true);
  };

  const menus: MenuItem[] = [
    {
      label: 'ARCHIVO',
      items: [
        { label: 'Guardar', shortcut: 'Ctrl+S', action: () => { onSave(); setOpenMenu(null); } },
        { label: 'Exportar JSON', action: exportarJSON },
        { label: 'Importar JSON', action: () => jsonFileInputRef.current?.click() },
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
        { label: 'Asistente IA (Chat)', action: () => { onOpenChat(); setOpenMenu(null); } },
        { label: 'Permisos de Acceso', action: () => { setShowPermisos(true); setOpenMenu(null); } },
        { label: 'Configuración de Cuenta & DB', action: () => { setShowSettings(true); setOpenMenu(null); } },
        { separator: true, action: () => {} },
        { 
          label: githubUsername ? `GitHub: Conectado (@${githubUsername})` : (isLoadingStatus ? 'Cargando GitHub...' : 'Vincular con GitHub'), 
          action: () => { if(!githubUsername && !isLoadingStatus) setShowSettings(true); setOpenMenu(null); } 
        },
        { label: 'Generar / Desplegar Backend', action: () => { openExportModal(); setOpenMenu(null); } },
      ]
    }
  ];

  return (
    <>
    <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".xml" onChange={importarEA} />
    <input type="file" ref={jsonFileInputRef} style={{ display: 'none' }} accept=".json" onChange={importarJSON} />
    <div className="menustrip" ref={menuRef}>
      {/* App brand */}
      <div className="menustrip__brand">
        <span className="menustrip__brand-icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-layers" aria-hidden="true"><path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"></path><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"></path><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"></path></svg></span>
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
        {(sala as any)?.isOfflineMode || !navigator.onLine ? (
          <div className="menustrip__offline-badge" title="Modo sin conexión: Almacenado localmente en IndexedDB">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="1" y1="1" x2="23" y2="23" />
              <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
              <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
              <path d="M10.71 5.05A16 16 0 0 1 22.58 9" />
              <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
              <line x1="12" y1="20" x2="12.01" y2="20" />
            </svg>
            <span>SIN CONEXIÓN</span>
          </div>
        ) : null}

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
          title="Guardar diagrama (Ctrl+S)"
        >
          {saving ? (
            <>
              <span className="menustrip__spinner-sm" />
              Guardando...
            </>
          ) : (
            <>
              <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              Guardar
            </>
          )}
        </button>

        {/* Deploy/Export Action */}
        <button 
          className="menustrip__export-btn" 
          onClick={openExportModal}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          Desplegar
        </button>

        {/* Share button */}
        <div className="menustrip__share-wrap">
          <button className="menustrip__share-btn" onClick={() => setShowShare(!showShare)}>
            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
            Compartir
          </button>
          {showShare && (
            <div className="menustrip__share-popover">
              <p className="menustrip__share-title">Enlace de acceso rápido</p>
              <div className="menustrip__share-input-wrap">
                <input type="text" readOnly value={shareLink} className="menustrip__share-input" />
                <button className="menustrip__share-copy-btn" onClick={copiarLink}>
                  {copiado ? <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg> : <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>}
                </button>
              </div>
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

      {showSettings && (
        <SettingsModal 
          onClose={() => setShowSettings(false)} 
        />
      )}

      {showExportModal && (
        <ExportModal
          proyectoId={sala.proyecto_id}
          proyectoNombre={sala.proyecto_nombre}
          githubRepoUrl={sala.github_repo_url}
          diagramState={getDiagramState()}
          onClose={() => setShowExportModal(false)}
          onSuccessNotification={showNotification}
        />
      )}

      {/* OVERLAY DE CARGA */}
      {isExporting && (
        <div className="menustrip__loading-overlay">
          <div className="menustrip__spinner"></div>
          <div className="menustrip__loading-text">
            Procesando y desplegando backend...
          </div>
        </div>
      )}

      {/* NOTIFICACIONES TOAST */}
      {notification && (
        <div className={`menustrip__toast menustrip__toast--${notification.type}`}>
          <div className="menustrip__toast-icon">
            {notification.type === 'success' ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            )}
          </div>
          <div className="menustrip__toast-message">{notification.message}</div>
          <button className="menustrip__toast-close" onClick={() => setNotification(null)}>&times;</button>
        </div>
      )}
    </>
  );
};
