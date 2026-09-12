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
import { apiFetch } from '@/shared/lib/api';
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

  const cargarProyectos = useCallback(async () => {
    try {
      const data = await proyectoService.listar();
      setProyectos(data);
    } catch {
      notificar({ tipo: 'error', titulo: 'Error', mensaje: 'No se pudieron cargar los proyectos.' });
    } finally {
      setLoading(false);
    }
  }, [notificar]);

  const cargarUsuario = useCallback(async () => {
    try {
      const data = await apiFetch('/usuarios/me');
      setUserName(data.nombre || data.email || 'Usuario');
    } catch {
      // No redirigir si /me falla; el token guard ya protege la ruta
      setUserName('Usuario');
    }
  }, []);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) { navigate('/login'); return; }
    cargarUsuario();
    cargarProyectos();
  }, [cargarProyectos, cargarUsuario, navigate]);

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
            <h1 className="dashboard-header__title">MIS PROYECTOS</h1>
            <p className="dashboard-header__sub">
              {proyectos.length} {proyectos.length === 1 ? 'proyecto' : 'proyectos'}
            </p>
          </div>
          <div className="dashboard-header__right">
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
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="dashboard-loading">
            <div className="dashboard-loading__spinner" />
            <p>Cargando proyectos...</p>
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
