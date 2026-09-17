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
        {/* Header */}
        <div className="dashboard-header">
          <div className="dashboard-header__left">
            <h1 className="dashboard-header__title">
              {isOffline ? 'MODO SIN CONEXIÓN' : 'MIS PROYECTOS'}
            </h1>
            <p className="dashboard-header__sub">
              {isOffline ? 'Estás trabajando localmente.' : `${proyectos.length} ${proyectos.length === 1 ? 'proyecto' : 'proyectos'}`}
            </p>
          </div>
          <div className="dashboard-header__right">
            {isOffline ? (
              <button className="dashboard-search__input" style={{cursor: 'pointer', background: '#ed8936', color: '#1a1d21', fontWeight: 'bold'}} onClick={() => navigate('/diagrama/local')}>
                IR A ENTORNO LOCAL
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
          <div className="dashboard-empty">
            <h2>Estás sin conexión a internet</h2>
            <p>Puedes crear un diagrama localmente y exportarlo a XML/JSON.</p>
            <button style={{marginTop: '20px', padding: '10px 20px', background: '#ed8936', color: 'black', fontWeight: 'bold'}} onClick={() => navigate('/diagrama/local')}>
              CREAR DIAGRAMA LOCAL
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
