import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DiagramProvider, useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { SalaSocketProvider } from '@/features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext';
import { Menustrip } from '@/features/gestion_modelado/lienzo_principal/components/Menustrip/Menustrip';
import { Toolbar } from '@/features/gestion_modelado/insertar_elemento/components/Toolbar/Toolbar';
import { DiagramCanvas } from '@/features/gestion_modelado/lienzo_principal/components/DiagramCanvas/DiagramCanvas';
import { MultiplayerCursors } from '@/features/gestion_salas/colaboracion_tiempo_real/components/MultiplayerCursors/MultiplayerCursors';
import { salaService } from '@/features/gestion_salas/shared/services/salaService';
import { PropertiesPanel } from '@/features/gestion_modelado/editar_elemento/components/PropertiesPanel/PropertiesPanel';
import type { SalaInfo } from '@/features/gestion_modelado/shared/types/types';
import './SalaView.css';

const SalaContent: React.FC<{ sala: SalaInfo }> = ({ sala }) => {
  const { loadDiagram, getDiagramState, isDirty } = useDiagram();
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const isGuest = new URLSearchParams(window.location.search).get('guest') === 'true';

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
    if (saving || isGuest) return;
    setSaving(true);
    try {
      await salaService.guardarLienzo(sala.proyecto_id, getDiagramState());
      isDirty.current = false;
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2500);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } finally {
      setSaving(false);
    }
  }, [saving, sala.proyecto_id, getDiagramState, isDirty]);

  const handleSaveRef = React.useRef(handleSave);
  useEffect(() => {
    handleSaveRef.current = handleSave;
  }, [handleSave]);

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
      <Menustrip sala={sala} onSave={handleSave} saving={saving} />

      <div className="sala-view__workspace">
        <Toolbar />
        <DiagramCanvas onCanvasClick={() => {}} />
        <MultiplayerCursors />
        <PropertiesPanel />
      </div>

      {/* Save status toast */}
      {saveStatus !== 'idle' && (
        <div className={`sala-view__save-toast sala-view__save-toast--${saveStatus}`}>
          {saveStatus === 'saved' ? <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polyline points="20 6 9 17 4 12"/></svg> Diagrama guardado</> : <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Error al guardar</>}
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
    if (!isGuest && !localStorage.getItem('access_token')) { 
      navigate('/login'); 
      return; 
    }
    if (!id) { navigate('/dashboard'); return; }

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
    <SalaSocketProvider sala={sala}>
      <DiagramProvider>
        <SalaContent sala={sala} />
      </DiagramProvider>
    </SalaSocketProvider>
  );
};
