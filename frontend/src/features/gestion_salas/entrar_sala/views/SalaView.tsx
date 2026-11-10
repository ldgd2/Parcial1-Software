import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { DiagramProvider, useDiagram, EVENTO_SINCRONIZADO } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { RealTimeSyncProvider, useRealTimeSync, getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { useRegistroCambiosManuales } from '@/features/gestion_asistencia_ia/gestionar_contexto_persistente';
import { useSugerenciasAutomaticas } from '@/features/gestion_asistencia_ia/generar_diagrama_prompt/hooks/useSugerenciasAutomaticas';
import { EVENTO_SOLICITUD_IA } from '@/features/gestion_asistencia_ia/generar_diagrama_prompt/utils/solicitudesIA';
import { GuardarPlantillaModal } from '@/features/gestion_proyectos/plantillas/GuardarPlantillaModal';
import { Menustrip } from '@/features/gestion_modelado/lienzo_principal/components/Menustrip/Menustrip';
import { Toolbar } from '@/features/gestion_modelado/insertar_elemento/components/Toolbar/Toolbar';
import { DiagramCanvas } from '@/features/gestion_modelado/lienzo_principal/components/DiagramCanvas/DiagramCanvas';
import { MultiplayerCursors } from '@/features/gestion_salas/colaboracion_tiempo_real/components/MultiplayerCursors/MultiplayerCursors';
import { ChatPanel } from '@/features/gestion_asistencia_ia/generar_diagrama_prompt/components/ChatPanel';
import { salaService } from '@/features/gestion_salas/shared/services/salaService';
import { PropertiesPanel } from '@/features/gestion_modelado/editar_elemento/components/PropertiesPanel/PropertiesPanel';
import { ChecklistPanel } from '@/features/gestion_asistencia_ia/gestionar_equipo_ia/components/ChecklistPanel/ChecklistPanel';
import { GestorEquipoIA } from '@/features/gestion_asistencia_ia/gestionar_equipo_ia/components/GestorEquipoIA/GestorEquipoIA';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import { ConflictModal } from '@/features/gestion_concurrencia/sincronizar_estado_local/components/ConflictModal/ConflictModal';
import type { SalaInfo } from '@/features/gestion_modelado/shared/types/types';
import './SalaView.css';

const SalaContent: React.FC<{ sala: SalaInfo }> = ({ sala }) => {
  const { loadDiagram, getDiagramState, isDirty } = useDiagram();
  const { roomUsers, isReadOnly } = useRealTimeSync();
  // Historial: registra los cambios que se hacen a mano en la pizarra (con su versión anterior)
  useRegistroCambiosManuales({
    proyectoId: sala.proyecto_id,
    autor: getUserIdentity().nickname,
    habilitado: !isReadOnly,
  });
  // CU33: la IA sugiere mejoras en el chat mientras se diagrama
  useSugerenciasAutomaticas({
    proyectoId: sala.proyecto_id,
    codigoAcceso: sala.codigo_acceso,
    habilitado: !isReadOnly,
  });
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const [isChatOpen, setIsChatOpen] = useState(false);
  // "Solucionar con IA" (u otro pedido externo) abre el chat, que envía el pedido
  useEffect(() => {
    const abrir = () => setIsChatOpen(true);
    window.addEventListener(EVENTO_SOLICITUD_IA, abrir);
    return () => window.removeEventListener(EVENTO_SOLICITUD_IA, abrir);
  }, []);
  const [isGestorOpen, setIsGestorOpen] = useState(false);
  const isGuest = new URLSearchParams(window.location.search).get('guest') === 'true';
  const isHost = sala.rol_proyecto === 'anfitrion';

  // Load diagram on mount
  useEffect(() => {
    if (sala.lienzo_json && sala.lienzo_json !== 'null') {
      try {
        const state = JSON.parse(sala.lienzo_json);
        loadDiagram(state);
      } catch {
        loadDiagram({ nodes: [], relations: [], version: 0 });
      }
    }
  }, [sala.lienzo_json, loadDiagram]);
  const handleSave = useCallback(async () => {
    // Un lector no guarda: el backend responde 403 y el autoguardado mostraría error cada 30 s
    if (saving || isGuest || isReadOnly) return;
    setSaving(true);
    try {
      if ((sala as any).isOfflineMode || !navigator.onLine) {
        const { offlineSyncService } = await import('@/features/gestion_concurrencia/sincronizar_estado_local/services/OfflineSyncService');
        offlineSyncService.saveLocalDiagramState(getDiagramState());
      } else {
        await salaService.guardarLienzo(sala.proyecto_id, getDiagramState());
      }
      isDirty.current = false;
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2500);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } finally {
      setSaving(false);
    }
  }, [saving, sala.proyecto_id, getDiagramState, isDirty, (sala as any).isOfflineMode, isGuest, isReadOnly]);
  const handleSaveRef = React.useRef(handleSave);
  useEffect(() => {
    handleSaveRef.current = handleSave;
  }, [handleSave]);

  // CU20: al volver la red y terminar la sincronización se avisa y se guarda enseguida
  // (antes no había aviso y lo hecho sin conexión se perdía al recargar).
  const [avisoSync, setAvisoSync] = useState<string | null>(null);
  useEffect(() => {
    const alSincronizar = (e: Event) => {
      const { conflictos } = (e as CustomEvent).detail || {};
      if (conflictos > 0) {
        setAvisoSync(`Modo en línea: hay ${conflictos} conflicto(s) por resolver antes de sincronizar.`);
        return;
      }
      setAvisoSync('Modo en línea: Todos los cambios han sido sincronizados');
      handleSaveRef.current();
      setTimeout(() => setAvisoSync(null), 5000);
    };
    window.addEventListener(EVENTO_SINCRONIZADO, alSincronizar);
    return () => window.removeEventListener(EVENTO_SINCRONIZADO, alSincronizar);
  }, []);

  // Avisos breves en la sala: proyecto recién creado (CU06/CU42) y alguien que entra (CU13)
  const location = useLocation();
  const mostrarAviso = useCallback((texto: string, ms = 5000) => {
    setAvisoSync(texto);
    setTimeout(() => setAvisoSync(actual => (actual === texto ? null : actual)), ms);
  }, []);
  useEffect(() => {
    const aviso = (location.state as { aviso?: string } | null)?.aviso;
    if (aviso) {
      mostrarAviso(aviso, 6000);
      window.history.replaceState({}, '');  // que no se repita al recargar
    }
  }, []);
  useEffect(() => {
    const alUnirse = (e: Event) => {
      const { nickname } = (e as CustomEvent).detail || {};
      mostrarAviso(`${nickname || 'Un colaborador'} se unió a la sala`);
    };
    window.addEventListener('sala_usuario_unido', alUnirse);
    return () => window.removeEventListener('sala_usuario_unido', alUnirse);
  }, [mostrarAviso]);

  // Autosave every 30s when dirty
  useEffect(() => {
    const interval = setInterval(() => {
      if (isDirty.current) {
        handleSaveRef.current();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [isDirty]);

  // Guardar al recargar/salir de la página
  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty.current) {
        handleSaveRef.current();
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [isDirty]);

  return (
    <div className="sala-view">
      <Menustrip sala={sala} onSave={handleSave} saving={saving} onOpenChat={() => setIsChatOpen(true)} />
      <GuardarPlantillaModal nombreProyecto={sala.proyecto_nombre} />

      <div className="sala-view__workspace">
        <Toolbar />
        {/* El panel de tareas se ancla al área del lienzo: al abrir el chat o
            el panel de propiedades el lienzo se encoge y el panel se mueve con él. */}
        <div className="sala-view__canvas-area">
          <DiagramCanvas onCanvasClick={() => {}} proyectoId={sala.proyecto_id} />
          {avisoSync && (
            <div role="status" className="sala-view__aviso-sync" style={{
              position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 20,
              background: '#e8f7ee', color: '#14532d', border: '1px solid #86d3a5', borderRadius: 8,
              padding: '6px 14px', fontSize: 13, pointerEvents: 'none', boxShadow: '0 2px 8px rgba(0,0,0,.12)'
            }}>
              {avisoSync}
            </div>
          )}
          {isReadOnly && (
            <div role="status" style={{
              position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)', zIndex: 20,
              background: '#fff7e6', color: '#7a4b00', border: '1px solid #f0c36d', borderRadius: 8,
              padding: '6px 14px', fontSize: 13, pointerEvents: 'none', boxShadow: '0 2px 8px rgba(0,0,0,.12)'
            }}>
              Modo lectura: el anfitrión te asignó como Lector, no puedes modificar el diagrama.
            </div>
          )}
          {sala.proyecto_id > 0 && !isGuest && (
            <ChecklistPanel
              proyectoId={sala.proyecto_id}
              isHost={isHost}
              onOpenGestor={() => setIsGestorOpen(true)}
            />
          )}
        </div>
        <MultiplayerCursors />
        <ChatPanel
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          codigoAcceso={sala.codigo_acceso}
          proyectoId={sala.proyecto_id}
          proyectoNombre={sala.proyecto_nombre}
        />
        <PropertiesPanel />
        <ConflictModal />
      </div>

      <Modal
        isOpen={isGestorOpen}
        onClose={() => setIsGestorOpen(false)}
        title="GESTOR DE EQUIPO IA"
        width="520px"
      >
        <GestorEquipoIA
          proyectoId={sala.proyecto_id}
          puedeAprobar={!isReadOnly}
          descripcionProyecto={sala.proyecto_nombre}
          colaboradoresIniciales={(() => {
            let currentUid = 1;
            try {
              const u = JSON.parse(localStorage.getItem('user') || '{}');
              if (u?.id) currentUid = Number(u.id);
            } catch {}
            const list: Array<{ usuario_id: number; nombre: string }> = [];
            if (roomUsers && roomUsers.length > 0) {
              roomUsers.forEach((u: { user_id?: number | string; id?: number | string; nickname?: string; nombre?: string }, i: number) => {
                const raw = String(u.user_id || u.id || '');
                const digits = raw.replace(/\D/g, '');
                const uid = digits ? parseInt(digits, 10) : (i + 2);
                list.push({
                  usuario_id: uid,
                  nombre: u.nickname || u.nombre || `Colaborador ${i + 1}`
                });
              });
            }
            if (!list.some(c => c.usuario_id === currentUid)) {
              list.unshift({
                usuario_id: currentUid,
                nombre: 'Yo (Anfitrión)'
              });
            }
            return list;
          })()}
        />
      </Modal>

      {/* Save status toast */}
      {saveStatus !== 'idle' && (
        <div className={`sala-view__save-toast sala-view__save-toast--${saveStatus}`}>
          {saveStatus === 'saved' ? <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polyline points="20 6 9 17 4 12"/></svg> Guardado</> : <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Error al guardar</>}
        </div>
      )}
    </div>
  );
};

export const SalaView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [sala, setSala] = useState<SalaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const isGuest = new URLSearchParams(window.location.search).get('guest') === 'true';
    
    import('@/shared/lib/TokenService').then(({ TokenService }) => {
      if (!isGuest && !TokenService.getToken()) { 
        navigate('/login'); 
        return; 
      }
      if (!id) { navigate('/dashboard'); return; }

      if (id === 'local' || !navigator.onLine) {
        // Modo local: cargar desde IndexedDB (via DiagramContext luego)
        import('@/features/gestion_concurrencia/sincronizar_estado_local/services/OfflineSyncService').then(async ({ offlineSyncService }) => {
            const localState = await offlineSyncService.getLocalDiagramState();
            setSala({
              proyecto_id: 0,
              proyecto_nombre: "Diagrama Local",
              codigo_acceso: "local",
              rol_proyecto: "anfitrion",
              isOfflineMode: true,
              lienzo_json: localState ? JSON.stringify(localState) : null
            } as any);
            setLoading(false);
        });
        return;
      }

      const loadData = isGuest 
        ? salaService.unirse(new URLSearchParams(window.location.search).get('codigo') || '')
            .then((data: any) => ({
               proyecto_id: data.proyecto_id,
               proyecto_nombre: data.proyecto_nombre,
               codigo_acceso: new URLSearchParams(window.location.search).get('codigo'),
               lienzo_json: null // Guest will get diagram via WS sync, or we can fetch it
            }))
        : salaService.cargarLienzo(Number(id));

      loadData
        .then((data) => setSala(data as SalaInfo))
        .catch((err) => setError(err.message || 'No tienes acceso a esta sala.'))
        .finally(() => setLoading(false));
    });
  }, [id, navigate]);


  if (loading) {
    return (
      <div className="sala-view sala-view--loading">
        <div className="sala-loading__spinner" />
        <p>Cargando sala...</p>
      </div>
    );
  }

  if (error || !sala) {
    return (
      <div className="sala-view sala-view--error">
        <div className="sala-error__icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></div>
        <h2>Sin acceso</h2>
        <p>{error || 'No se pudo cargar la sala.'}</p>
        <button onClick={() => navigate('/dashboard')}>Volver al Dashboard</button>
      </div>
    );
  }

  return (
    <RealTimeSyncProvider sala={sala}>
      <DiagramProvider>
        <SalaContent sala={sala} />
      </DiagramProvider>
    </RealTimeSyncProvider>
  );
};
