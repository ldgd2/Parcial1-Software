import React, { useState } from 'react';
import { useExportarGithub } from '@/features/gestion_asistencia_ia/exportar_github/hooks/useExportarGithub';
import './ExportModal.css';

interface Props {
  proyectoId: number;
  proyectoNombre: string;
  githubRepoUrl?: string | null;
  diagramState: any;
  onClose: () => void;
  onSuccessNotification?: (type: 'success' | 'error', message: string) => void;
}

export const ExportModal: React.FC<Props> = ({
  proyectoId,
  proyectoNombre,
  githubRepoUrl,
  diagramState,
  onClose,
  onSuccessNotification
}) => {
  const { githubUsername, isExporting, exportarProyecto } = useExportarGithub();

  const defaultRepo = githubRepoUrl
    ? githubRepoUrl.split('/').pop()?.replace('.git', '') || proyectoNombre.toLowerCase().replace(/[^a-z0-9]/g, '-')
    : proyectoNombre.toLowerCase().replace(/[^a-z0-9]/g, '-');

  const [repoName, setRepoName] = useState(defaultRepo);
  const [autoDeploy, setAutoDeploy] = useState(true);
  const [result, setResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!repoName.trim()) {
      setErrorMsg("El nombre del repositorio no puede estar vacío.");
      return;
    }

    try {
      const res = await exportarProyecto(proyectoId, repoName.trim(), diagramState, autoDeploy);
      if (res) {
        setResult(res);
        if (onSuccessNotification) {
          onSuccessNotification('success', res.mensaje || 'Proyecto exportado con éxito');
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Ocurrió un error al exportar el proyecto.");
    }
  };

  const handleDownloadApiDocs = () => {
    if (!result?.api_docs_md) return;
    const blob = new Blob([result.api_docs_md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `API_Docs_${repoName}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="export-modal-overlay">
      <div className="export-modal-card">
        <div className="export-modal-header">
          <div className="export-modal-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            <h2>Exportar & Desplegar Backend</h2>
          </div>
          <button className="export-modal-close" onClick={onClose}>&times;</button>
        </div>

        {!result ? (
          <form onSubmit={handleExport} className="export-modal-body">
            {!githubUsername ? (
              <div className="export-warning-banner">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span>Atención: Necesitas vincular tu cuenta de GitHub primero en la Configuración del Perfil.</span>
              </div>
            ) : null}

            {errorMsg && (
              <div className="export-error-banner">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="export-field-group">
              <label>Nombre del Repositorio GitHub</label>
              <div className="export-input-wrapper">
                <span className="export-input-prefix">{githubUsername || 'usuario'}/</span>
                <input
                  type="text"
                  value={repoName}
                  onChange={(e) => setRepoName(e.target.value)}
                  placeholder="mi-proyecto-backend"
                  required
                />
              </div>
            </div>

            <div className="export-options-grid">
              <div
                className={`export-option-card ${autoDeploy ? 'active' : ''}`}
                onClick={() => setAutoDeploy(true)}
              >
                <div className="option-radio">
                  <div className="option-radio-dot" />
                </div>
                <div className="option-content">
                  <div className="option-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                    <span>GitHub + Auto-Alojamiento</span>
                  </div>
                  <p>Genera el código Spring Boot, crea el repo en GitHub y despliega automáticamente con Base de Datos PostgreSQL en Gerlextech Host.</p>
                </div>
              </div>

              <div
                className={`export-option-card ${!autoDeploy ? 'active' : ''}`}
                onClick={() => setAutoDeploy(false)}
              >
                <div className="option-radio">
                  <div className="option-radio-dot" />
                </div>
                <div className="option-content">
                  <div className="option-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                    <span>Solo Exportar a GitHub</span>
                  </div>
                  <p>Genera la estructura de código fuente Java/Spring Boot e sube el repositorio únicamente a tu cuenta de GitHub.</p>
                </div>
              </div>
            </div>

            <div className="export-modal-footer">
              <button type="button" className="export-btn-cancel" onClick={onClose}>
                Cancelar
              </button>
              <button
                type="submit"
                className="export-btn-submit"
                disabled={isExporting || !githubUsername}
              >
                {isExporting ? (
                  <>
                    <span className="export-btn-spinner" />
                    <span>Procesando...</span>
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                    <span>{autoDeploy ? 'Exportar & Desplegar' : 'Exportar a GitHub'}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="export-modal-success-body">
            <div className="success-icon-badge">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>

            <h2>¡Exportación Completada!</h2>
            <p className="success-message">{result.mensaje || 'Tu backend Spring Boot ha sido procesado exitosamente.'}</p>

            <div className="success-links-list">
              {result.repo_url && (
                <a href={result.repo_url} target="_blank" rel="noopener noreferrer" className="success-link-card">
                  <div className="link-info">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 22v-4a48 48 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/></svg>
                    <div>
                      <strong>Repositorio GitHub</strong>
                      <span>{result.repo_url}</span>
                    </div>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
                </a>
              )}

              {result.deployed_url && (
                <a href={result.deployed_url} target="_blank" rel="noopener noreferrer" className="success-link-card highlight">
                  <div className="link-info">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <div>
                      <strong>Servicio Desplegado (Base API)</strong>
                      <span>{result.deployed_url}</span>
                    </div>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
                </a>
              )}

              {result.deployed_url && (
                <a href={`${result.deployed_url.replace(/\/$/, '')}/help`} target="_blank" rel="noopener noreferrer" className="success-link-card">
                  <div className="link-info">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                    <div>
                      <strong>Documentación Swagger UI</strong>
                      <span>{result.deployed_url.replace(/\/$/, '')}/help</span>
                    </div>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
                </a>
              )}
            </div>

            {result.api_docs_md && (
              <button className="export-btn-download" onClick={handleDownloadApiDocs}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>Descargar API_Docs.md</span>
              </button>
            )}

            <button className="export-btn-cancel" style={{ width: '100%', marginTop: '1rem' }} onClick={onClose}>
              Cerrar
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
