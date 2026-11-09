import React, { useEffect } from 'react';
import { Database, Copy, Check, Download, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import { useGenerarSeeders } from '../hooks/useGenerarSeeders';
import type { ClassNode, Relation } from '@/features/gestion_modelado/shared/types/types';
import './SeedersModal.css';

interface SeedersModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: ClassNode[];
  relations: Relation[];
  proyectoId?: number;
}

const CANTIDADES = [5, 10, 20, 50];

export const SeedersModal: React.FC<SeedersModalProps> = ({
  isOpen,
  onClose,
  nodes,
  relations,
  proyectoId
}) => {
  const {
    loading,
    cantidad,
    setCantidad,
    formato,
    setFormato,
    resultado,
    errorMessage,
    copied,
    ejecutarGeneracion,
    copiarAlPortapapeles,
    descargarArchivo
  } = useGenerarSeeders({ nodes, relations, proyectoId });

  useEffect(() => {
    if (isOpen) {
      ejecutarGeneracion();
    }
  }, [isOpen, cantidad, formato]);

  if (!isOpen) return null;

  const codigoActual = resultado
    ? (formato === 'sql' ? resultado.sql_script : (resultado.java_code || resultado.sql_script))
    : '';

  const footer = (
    <>
      <span className="seeders__total">
        {resultado && (
          <>
            <strong>{resultado.total_registros}</strong> registros en <strong>{resultado.total_tablas}</strong> tablas
          </>
        )}
      </span>
      <button
        type="button"
        className="modal-btn"
        onClick={copiarAlPortapapeles}
        disabled={!resultado || loading}
      >
        {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
        <span>{copied ? 'Copiado' : 'Copiar script'}</span>
      </button>
      <button
        type="button"
        className="modal-btn modal-btn--primary"
        onClick={descargarArchivo}
        disabled={!resultado || loading}
      >
        <Download size={14} aria-hidden="true" />
        <span>Descargar archivo</span>
      </button>
    </>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      width="900px"
      className="seeders-modal"
      bodyClassName="modal-body--flush"
      footer={footer}
      title={
        <>
          <Database size={18} aria-hidden="true" />
          Generador de seeders
        </>
      }
    >
      <p className="seeders__intro">
        Datos de prueba coherentes para tu base de datos, insertados en orden según sus claves foráneas.
      </p>

      {/* Controles */}
      <div className="seeders__controles">
        <div className="seeders__control">
          <span className="seeders__label" id="seeders-cantidad">REGISTROS POR TABLA</span>
          <div className="seeders__segmentado" role="group" aria-labelledby="seeders-cantidad">
            {CANTIDADES.map(c => (
              <button
                key={c}
                type="button"
                className={cantidad === c ? 'is-active' : ''}
                aria-pressed={cantidad === c}
                onClick={() => setCantidad(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div className="seeders__control">
          <span className="seeders__label" id="seeders-formato">FORMATO</span>
          <div className="seeders__segmentado" role="group" aria-labelledby="seeders-formato">
            <button
              type="button"
              className={formato === 'sql' ? 'is-active' : ''}
              aria-pressed={formato === 'sql'}
              onClick={() => setFormato('sql')}
            >
              PostgreSQL (.sql)
            </button>
            <button
              type="button"
              className={formato === 'java_runner' ? 'is-active' : ''}
              aria-pressed={formato === 'java_runner'}
              onClick={() => setFormato('java_runner')}
            >
              Spring Boot (Java)
            </button>
          </div>
        </div>
      </div>

      {/* Contenido */}
      {loading ? (
        <div className="seeders__estado">
          <Loader2 size={28} className="seeders__spin" aria-hidden="true" />
          <p>Generando datos de prueba…</p>
        </div>
      ) : errorMessage ? (
        <div className="seeders__estado seeders__estado--error" role="alert">
          <AlertCircle size={28} aria-hidden="true" />
          <p>{errorMessage}</p>
        </div>
      ) : (
        <>
          {resultado && (
            <div className="seeders__resumen">
              <span className="seeders__resumen-texto">
                <CheckCircle2 size={15} aria-hidden="true" />
                {resultado.resumen}
              </span>
              <span className="seeders__orden" title={resultado.orden_insercion.join(' → ')}>
                Orden: {resultado.orden_insercion.slice(0, 4).join(' → ')}
                {resultado.orden_insercion.length > 4 ? ' …' : ''}
              </span>
            </div>
          )}
          <pre className="seeders__codigo">{codigoActual}</pre>
        </>
      )}
    </Modal>
  );
};
