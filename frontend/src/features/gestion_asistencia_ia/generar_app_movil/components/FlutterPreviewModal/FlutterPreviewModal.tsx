import React, { useState, useEffect } from 'react';
import { useAppMovil } from '../../hooks/useAppMovil';
import { descargarZipAppMovil } from '../../services/appMovilService';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import './FlutterPreviewModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  proyectoId: number;
  diagramJson: Record<string, any>;
  apiBaseUrl?: string;
}

export const FlutterPreviewModal: React.FC<Props> = ({
  isOpen,
  onClose,
  proyectoId,
  diagramJson,
  apiBaseUrl = 'http://localhost:8080',
}) => {
  const {
    loading,
    error,
    appData,
    selectedFile,
    setSelectedFile,
    refining,
    refinementSuccess,
    generar,
    refinar,
  } = useAppMovil(proyectoId);

  const [promptRefine, setPromptRefine] = useState('');
  const [copiado, setCopiado] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);

  const handleDescargarZip = async () => {
    setDownloadingZip(true);
    try {
      await descargarZipAppMovil(proyectoId, apiBaseUrl);
    } catch (e) {
      console.error('Error al descargar ZIP:', e);
    } finally {
      setDownloadingZip(false);
    }
  };

  useEffect(() => {
    if (isOpen && !appData) {
      generar(diagramJson, apiBaseUrl);
    }
  }, [isOpen, appData, generar, diagramJson, apiBaseUrl]);

  if (!isOpen) return null;

  const archivos = appData?.archivos || {};
  const listaArchivos = Object.keys(archivos);
  const contenidoActual = selectedFile ? archivos[selectedFile] || '' : '';

  const handleCopiar = async () => {
    if (!contenidoActual) return;
    await navigator.clipboard.writeText(contenidoActual);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  const handleRefinar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptRefine.trim() || !selectedFile) return;
    const vistaNombre = selectedFile.split('/').pop() || selectedFile;
    await refinar(vistaNombre, contenidoActual, promptRefine.trim());
    setPromptRefine('');
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      width="950px"
      className="flutter-modal-panel"
      bodyClassName="modal-body--flush"
      title={
        <>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
            <line x1="12" y1="18" x2="12.01" y2="18" />
          </svg>
          App móvil Flutter
        </>
      }
      headerActions={
        <>
          <span className="flutter-badge">{listaArchivos.length} archivos</span>
          <button
            type="button"
            className="modal-btn modal-btn--primary flutter-zip-btn"
            onClick={handleDescargarZip}
            disabled={downloadingZip || listaArchivos.length === 0}
            title="Descargar proyecto completo en ZIP"
          >
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>{downloadingZip ? "Comprimiendo..." : "Descargar ZIP"}</span>
          </button>
        </>
      }
    >
        {loading ? (
          <div className="flutter-empty-view">
            <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 14 14" />
            </svg>
            <p>Generando esqueleto y componentes Flutter...</p>
          </div>
        ) : error ? (
          <div className="flutter-empty-view">
            <svg viewBox="0 0 24 24" width="36" height="36" fill="none" style={{ stroke: 'var(--danger)' }} strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            <p style={{ color: 'var(--danger)' }}>{error}</p>
          </div>
        ) : (
          <div className="flutter-modal-body">
            {/* Sidebar lista de archivos */}
            <div className="flutter-files-sidebar">
              <div className="flutter-files-header">
                Estructura del Proyecto
              </div>
              {listaArchivos.map((archivo) => (
                <div
                  key={archivo}
                  className={`flutter-file-item ${selectedFile === archivo ? 'active' : ''}`}
                  onClick={() => setSelectedFile(archivo)}
                  title={archivo}
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                    <polyline points="13 2 13 9 20 9" />
                  </svg>
                  <span className="flutter-file-path">{archivo}</span>
                </div>
              ))}
            </div>

            {/* Panel de código */}
            <div className="flutter-editor-pane">
              <div className="flutter-editor-toolbar">
                <span className="flutter-current-file">{selectedFile}</span>
                <div className="flutter-editor-actions">
                  <button className="flutter-action-btn" onClick={handleCopiar}>
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                    <span>{copiado ? 'Copiado' : 'Copiar Archivo'}</span>
                  </button>
                </div>
              </div>

              <pre className="flutter-code-view">{contenidoActual}</pre>

              {/* Caja de refinamiento con IA optimizada */}
              <form onSubmit={handleRefinar} className="flutter-refine-box">
                <input
                  type="text"
                  className="flutter-refine-input"
                  placeholder="Pedir a la IA personalizar esta vista/modelo (ej: agregar filtro por estado)..."
                  value={promptRefine}
                  onChange={(e) => setPromptRefine(e.target.value)}
                  disabled={refining}
                />
                <button
                  type="submit"
                  className="flutter-refine-btn"
                  disabled={refining || !promptRefine.trim()}
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                  </svg>
                  <span>{refining ? 'Refinando...' : 'Refinar con IA'}</span>
                </button>
              </form>
              {refinementSuccess && (
                <div style={{ padding: '6px 16px', fontSize: '0.75rem', color: 'var(--success)', background: 'rgba(16, 185, 129, 0.12)' }}>
                  {refinementSuccess}
                </div>
              )}
            </div>
          </div>
        )}
    </Modal>
  );
};
