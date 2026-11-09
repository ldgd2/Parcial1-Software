import React, { useEffect } from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, Info, Check, Zap, RefreshCw, Loader2 } from 'lucide-react';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import { useDetectarErrores } from '../hooks/useDetectarErrores';
import './ErrorDetectionModal.css';

interface ErrorDetectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: any[];
  relations: any[];
  onApplyCorrections: (fixedNodes: any[], fixedRelations: any[]) => void;
  xmlContent?: string;
}

const TIPOS: Record<string, string> = {
  sin_pk: 'Sin clave primaria (PK)',
  fk_huerfana: 'FK huérfana',
  tipo_discordante: 'Tipo discordante',
  dependencia_circular: 'Dependencia circular',
  relacion_nm_directa: 'Relación N:M directa',
  tabla_aislada: 'Tabla aislada',
  palabra_reservada: 'Palabra reservada SQL'
};

const Severidad: React.FC<{ sev: string }> = ({ sev }) => {
  const nivel = sev === 'alta' ? 'alta' : sev === 'media' ? 'media' : 'baja';
  const Icono = nivel === 'alta' ? AlertTriangle : nivel === 'media' ? AlertCircle : Info;
  return (
    <span className={`errores__sev errores__sev--${nivel}`}>
      <Icono size={12} aria-hidden="true" />
      {nivel === 'alta' ? 'Alta' : nivel === 'media' ? 'Media' : 'Baja'}
    </span>
  );
};

const Tipo: React.FC<{ tipo: string }> = ({ tipo }) => (
  <span className="errores__tipo">{TIPOS[tipo] || tipo}</span>
);

export const ErrorDetectionModal: React.FC<ErrorDetectionModalProps> = ({
  isOpen,
  onClose,
  nodes,
  relations,
  onApplyCorrections,
  xmlContent
}) => {
  const {
    loading,
    repairing,
    errorReport,
    selectedError,
    setSelectedError,
    errorMessage,
    ejecutarAnalisis,
    ejecutarReparacion
  } = useDetectarErrores({ nodes, relations, onApplyCorrections });

  useEffect(() => {
    if (isOpen) {
      ejecutarAnalisis(xmlContent);
    }
  }, [isOpen, ejecutarAnalisis, xmlContent]);

  if (!isOpen) return null;

  const hayErrores = !!errorReport && errorReport.total_errores > 0;

  const footer = (
    <>
      {hayErrores && (
        <span className="errores__pie-nota">
          Se aplicarán arreglos automáticos a las {errorReport!.total_errores} inconsistencias
        </span>
      )}
      <button type="button" className="modal-btn" onClick={onClose}>Cerrar</button>
      {hayErrores && (
        <button
          type="button"
          className="modal-btn modal-btn--primary"
          disabled={repairing}
          onClick={() => ejecutarReparacion(undefined, xmlContent)}
        >
          {repairing
            ? <><Loader2 size={14} className="errores__spin" aria-hidden="true" /> Reparando…</>
            : <><RefreshCw size={14} aria-hidden="true" /> Reparar automáticamente</>}
        </button>
      )}
    </>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      width="960px"
      className="errores-modal"
      bodyClassName="modal-body--flush"
      footer={footer}
      title={
        <>
          <ShieldCheck size={18} aria-hidden="true" />
          Diagnóstico de errores en la BD
        </>
      }
    >
      <p className="errores__intro">
        Revisa el esquema (lienzo o XML de Enterprise Architect) en busca de inconsistencias relacionales.
      </p>

      {loading ? (
        <div className="errores__estado">
          <Loader2 size={28} className="errores__spin" aria-hidden="true" />
          <p>Analizando el esquema…</p>
        </div>
      ) : errorMessage ? (
        <div className="errores__estado errores__estado--error" role="alert">
          <AlertCircle size={28} aria-hidden="true" />
          <p>{errorMessage}</p>
          <button type="button" className="modal-btn" onClick={() => ejecutarAnalisis(xmlContent)}>
            Reintentar
          </button>
        </div>
      ) : !hayErrores ? (
        <div className="errores__estado">
          <div className="errores__ok" aria-hidden="true"><Check size={26} /></div>
          <h3 className="errores__ok-titulo">Esquema consistente</h3>
          <p>
            No hay claves foráneas huérfanas, tablas sin PK, ciclos directos ni relaciones N:M sin resolver.
            El modelo está listo para migraciones SQL.
          </p>
        </div>
      ) : (
        <div className="errores__layout">
          {/* Lista de errores */}
          <div className="errores__lista">
            <div className="errores__lista-head">
              <span>{errorReport!.total_errores} inconsistencias</span>
              <span className="errores__stats">
                <span className="is-alta">{errorReport!.estadisticas.sin_pk || 0} sin PK</span>
                <span aria-hidden="true">·</span>
                <span className="is-media">{errorReport!.estadisticas.fk_huerfana || 0} FK</span>
              </span>
            </div>
            <ul role="listbox" aria-label="Errores detectados">
              {errorReport!.errores.map(err => {
                const activo = selectedError?.id === err.id;
                return (
                  <li key={err.id}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={activo}
                      className={`errores__item errores__item--${err.severidad === 'alta' ? 'alta' : err.severidad === 'media' ? 'media' : 'baja'}${activo ? ' is-active' : ''}`}
                      onClick={() => setSelectedError(err)}
                    >
                      <span className="errores__item-head">
                        <span className="errores__tabla">{err.tabla}</span>
                        <Severidad sev={err.severidad} />
                      </span>
                      <Tipo tipo={err.tipo} />
                      <span className="errores__desc">{err.descripcion}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Detalle */}
          <div className="errores__detalle">
            {selectedError ? (
              <>
                <div className="errores__detalle-head">
                  <div>
                    <h3 className="errores__detalle-titulo">
                      {selectedError.tabla}
                      <Severidad sev={selectedError.severidad} />
                    </h3>
                    <p className="errores__detalle-id">
                      ID: {selectedError.id}
                      {selectedError.columna && ` · Atributo: ${selectedError.columna}`}
                    </p>
                  </div>
                  <Tipo tipo={selectedError.tipo} />
                </div>

                <section className="errores__bloque">
                  <h4 className="errores__label">DESCRIPCIÓN</h4>
                  <p className="errores__caja">{selectedError.descripcion}</p>
                </section>

                <section className="errores__bloque">
                  <h4 className="errores__label">SOLUCIÓN SUGERIDA</h4>
                  <p className="errores__caja errores__caja--solucion">
                    <Zap size={16} aria-hidden="true" />
                    <span>{selectedError.solucion_sugerida}</span>
                  </p>
                </section>
              </>
            ) : (
              <div className="errores__estado">
                <p>Selecciona un error para ver el detalle.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </Modal>
  );
};
