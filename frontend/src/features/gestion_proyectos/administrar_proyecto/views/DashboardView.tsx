import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardBackground } from '../components/DashboardBackground/DashboardBackground';
import { DashboardNavbar } from '../components/DashboardNavbar/DashboardNavbar';
import { ProyectoCard } from '../components/ProyectoCard/ProyectoCard';
import { NuevoProyectoCard } from '@/features/gestion_proyectos/crear_proyecto/components/NuevoProyectoCard/NuevoProyectoCard';
import { ProyectoFormModal } from '@/features/gestion_proyectos/crear_proyecto/components/ProyectoFormModal/ProyectoFormModal';
import { CompartirModal } from '@/features/gestion_proyectos/compartir_proyecto/components/CompartirModal/CompartirModal';
import { ToastStack } from '../components/ToastStack/ToastStack';
import { Modal } from '../components/Modal/Modal';
import { NotifProvider, useNotif } from '@/features/gestion_proyectos/shared/context/NotifContext';
import { proyectoService } from '@/features/gestion_proyectos/shared/utils/proyectoService';
import type { Proyecto } from '@/features/gestion_proyectos/shared/utils/types';
import { apiFetch, API_URL } from '@/shared/lib/api';
import './DashboardView.css';

// Inner component to access context
const DashboardContent: React.FC = () => {
  const navigate = useNavigate();
  const { notificar } = useNotif();

  const [proyectos, setProyectos] = useState<Proyecto[]>([]);
  const [loading, setLoading] = useState(true);
  const [userName, setUserName] = useState('Usuario');
  const [busqueda, setBusqueda] = useState('');

  // Modal states
  const [modalCrear, setModalCrear] = useState(false);
  const [proyectoEditar, setProyectoEditar] = useState<Proyecto | null>(null);
  const [proyectoCompartir, setProyectoCompartir] = useState<Proyecto | null>(null);
  const [proyectoEliminar, setProyectoEliminar] = useState<Proyecto | null>(null);
  const [eliminando, setEliminando] = useState(false);

  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const onOnline = () => {
      // Intentamos hacer ping al backend antes de volver online
      fetch(`${API_URL}/docs`, { method: 'HEAD' })
        .then(() => setIsOffline(false))
        .catch(() => setIsOffline(true));
    };
    const onOffline = () => setIsOffline(true);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  const cargarProyectos = useCallback(async () => {
    if (isOffline) {
      setProyectos([]);
      setLoading(false);
      return;
    }
    try {
      const data = await proyectoService.listar();
      setProyectos(data);
    } catch {
      notificar({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudieron cargar los proyectos.' });
    } finally {
      setLoading(false);
    }
  }, [notificar, isOffline]);

  const checkBackendAndAuth = useCallback(async () => {
    if (!navigator.onLine) {
      setIsOffline(true);
      setLoading(false);
      return;
    }

    try {
      // Intentamos acceder a una ruta para ver si el backend responde
      await fetch(`${API_URL}/docs`, { method: 'HEAD' });
      setIsOffline(false);
      
      const { TokenService } = await import('@/shared/lib/TokenService');
      if (!TokenService.getToken()) {
        navigate('/login');
        return;
      }
      
      try {
        const data = await apiFetch('/usuarios/me');
        setUserName(data.nombre || data.email || 'Usuario');
      } catch {
        setUserName('Usuario');
      }
      
      await cargarProyectos();
      
    } catch (e: any) {
      // Si falla el fetch por red, asumimos que el backend está muerto
      console.warn('Backend inalcanzable, activando modo offline', e);
      setIsOffline(true);
      setLoading(false);
    }
  }, [cargarProyectos, navigate]);

  useEffect(() => {
    checkBackendAndAuth();
  }, [checkBackendAndAuth]);

  const handleCrear = async (nombre: string, descripcion: string) => {
    const nuevo = await proyectoService.crear(nombre, descripcion);
    setProyectos(prev => [nuevo, ...prev]);
    notificar({
      tipo: 'exito',
      titulo: 'Proyecto creado',
      mensaje: `"${nuevo.nombre}" listo. Comparte el enlace para colaborar.`,
    });
    // Auto-open share
    setTimeout(() => setProyectoCompartir(nuevo), 400);
  };

  const handleEditar = async (nombre: string, descripcion: string) => {
    if (!proyectoEditar) return;
    const actualizado = await proyectoService.actualizar(proyectoEditar.id, nombre, descripcion);
    setProyectos(prev => prev.map(p => (p.id === actualizado.id ? actualizado : p)));
    notificar({ tipo: 'exito', titulo: 'Proyecto actualizado', mensaje: `"${actualizado.nombre}" guardado correctamente.` });
  };

  const handleEliminar = async () => {
    if (!proyectoEliminar) return;
    setEliminando(true);
    try {
      await proyectoService.eliminar(proyectoEliminar.id);
      setProyectos(prev => prev.filter(p => p.id !== proyectoEliminar.id));
      notificar({ tipo: 'info', titulo: 'Proyecto eliminado', mensaje: `"${proyectoEliminar.nombre}" fue eliminado.` });
      setProyectoEliminar(null);
    } catch (err: any) {
      notificar({ tipo: 'error', titulo: 'Error', mensaje: err.message || 'No se pudo eliminar.' });
    } finally {
      setEliminando(false);
    }
  };

  const proyectosFiltrados = proyectos.filter(p =>
    p.nombre.toLowerCase().includes(busqueda.toLowerCase())
  );

  return (
    <div className="dashboard-view">
      <DashboardBackground />
      <DashboardNavbar userName={userName} />

      <main className="dashboard-main">
        {/* Offline Banner */}
        {isOffline && (
          <div className="dashboard-offline-banner">
            <div className="dashboard-offline-banner__left">
              <div className="dashboard-offline-banner__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="1" y1="1" x2="23" y2="23" />
                  <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
                  <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
                  <path d="M10.71 5.05A16 16 0 0 1 22.58 9" />
                  <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
                  <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
                  <line x1="12" y1="20" x2="12.01" y2="20" />
                </svg>
              </div>
              <div className="dashboard-offline-banner__text">
                <strong>MODO SIN CONEXIÓN ACTIVO</strong>
                <p>El servidor no está accesible. Puedes continuar trabajando localmente; los diagramas se guardarán en IndexedDB.</p>
              </div>
            </div>
            <button className="dashboard-btn-offline" onClick={() => navigate('/diagrama/local')}>
              <span>Abrir Entorno Local</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </button>
          </div>
        )}

        {/* Header */}
        <div className="dashboard-header">
          <div className="dashboard-header__left">
            <h1 className="dashboard-header__title">
              {isOffline ? 'PROYECTOS LOCALES' : 'MIS PROYECTOS'}
            </h1>
            <p className="dashboard-header__sub">
              {isOffline ? 'Almacenamiento persistente en IndexedDB.' : `${proyectos.length} ${proyectos.length === 1 ? 'proyecto' : 'proyectos'}`}
            </p>
          </div>
          <div className="dashboard-header__right">
            {isOffline ? (
              <button className="dashboard-btn-offline-secondary" onClick={() => navigate('/diagrama/local')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
                <span>Nuevo Diagrama Local</span>
              </button>
            ) : (
              <div className="dashboard-search">
                <span className="dashboard-search__icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
                <input
                  id="input-buscar-proyecto"
                  className="dashboard-search__input"
                  type="text"
                  placeholder="BUSCAR..."
                  value={busqueda}
                  onChange={e => setBusqueda(e.target.value)}
                />
              </div>
            )}
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="dashboard-loading">
            <div className="dashboard-loading__spinner" />
            <p>Cargando proyectos...</p>
          </div>
        ) : isOffline ? (
          <div className="dashboard-empty dashboard-empty--offline">
            <div className="dashboard-empty__badge">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="1" y1="1" x2="23" y2="23" />
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
                <path d="M10.71 5.05A16 16 0 0 1 22.58 9" />
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
                <line x1="12" y1="20" x2="12.01" y2="20" />
              </svg>
            </div>
            <h2>Estás Trabajando sin Conexión</h2>
            <p>Puedes crear diagramas de clase UML localmente y exportarlos a formatos XML o JSON en cualquier momento.</p>
            <button className="dashboard-btn-offline-action" onClick={() => navigate('/diagrama/local')}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
              <span>Crear Diagrama Local</span>
            </button>
          </div>
        ) : (
          <div className="dashboard-grid">
            <NuevoProyectoCard onClick={() => setModalCrear(true)} />
            {proyectosFiltrados.map((p, i) => (
              <div key={p.id} style={{ animationDelay: `${i * 0.06}s` }}>
                <ProyectoCard
                  proyecto={p}
                  onAbrir={() => navigate(`/diagrama/${p.id}`)}
                  onEditar={() => setProyectoEditar(p)}
                  onCompartir={() => setProyectoCompartir(p)}
                  onEliminar={() => setProyectoEliminar(p)}
                />
              </div>
            ))}
            {proyectosFiltrados.length === 0 && busqueda && (
              <div className="dashboard-empty">
                <span>Sin resultados para "{busqueda}"</span>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modals */}
      <ProyectoFormModal
        isOpen={modalCrear}
        onClose={() => setModalCrear(false)}
        onSubmit={handleCrear}
      />
      <ProyectoFormModal
        isOpen={!!proyectoEditar}
        onClose={() => setProyectoEditar(null)}
        onSubmit={handleEditar}
        proyectoInicial={proyectoEditar}
      />
      <CompartirModal
        isOpen={!!proyectoCompartir}
        onClose={() => setProyectoCompartir(null)}
        proyecto={proyectoCompartir}
      />

      {/* Confirm Delete Modal */}
      <Modal
        isOpen={!!proyectoEliminar}
        onClose={() => setProyectoEliminar(null)}
        title="CONFIRMAR ELIMINACIÓN"
        width="400px"
      >
        <div className="dashboard-confirm-delete">
          <p>
            ¿Eliminar permanentemente <strong>"{proyectoEliminar?.nombre}"</strong>?
            Esta acción no puede deshacerse.
          </p>
          <div className="dashboard-confirm-delete__actions">
            <button
              className="dashboard-confirm-delete__cancel"
              onClick={() => setProyectoEliminar(null)}
            >
              CANCELAR
            </button>
            <button
              id="btn-confirmar-eliminar"
              className="dashboard-confirm-delete__confirm"
              onClick={handleEliminar}
              disabled={eliminando}
            >
              {eliminando ? '...' : 'ELIMINAR'}
            </button>
          </div>
        </div>
      </Modal>

      <ToastStack />
    </div>
  );
};

// Wrap with provider
export const DashboardView: React.FC = () => (
  <NotifProvider>
    <DashboardContent />
  </NotifProvider>
);
