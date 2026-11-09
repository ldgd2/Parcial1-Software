import React, { useState, useEffect } from 'react';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import type { Proyecto } from '@/features/gestion_proyectos/shared/utils/types';
import { listarPlantillas, type PlantillaMeta } from '@/features/gestion_proyectos/plantillas/plantillas';
import '@/features/gestion_proyectos/plantillas/plantillas.css';
import './ProyectoFormModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (nombre: string, descripcion: string, plantillaId?: string) => Promise<void>;
  proyectoInicial?: Proyecto | null;
}

export const ProyectoFormModal: React.FC<Props> = ({ isOpen, onClose, onSubmit, proyectoInicial }) => {
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [plantillas, setPlantillas] = useState<PlantillaMeta[]>([]);
  const [plantillaId, setPlantillaId] = useState('');

  // CU42: plantillas solo al crear
  useEffect(() => {
    if (!isOpen || proyectoInicial) return;
    setPlantillaId('');
    listarPlantillas().then(setPlantillas).catch(() => setPlantillas([]));
  }, [isOpen, proyectoInicial]);

  useEffect(() => {
    if (proyectoInicial) {
      setNombre(proyectoInicial.nombre);
      setDescripcion(proyectoInicial.descripcion ?? '');
    } else {
      setNombre('');
      setDescripcion('');
    }
    setError('');
  }, [proyectoInicial, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) { setError('El nombre es requerido.'); return; }
    setLoading(true);
    setError('');
    try {
      await onSubmit(nombre.trim(), descripcion.trim(), plantillaId || undefined);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error al guardar.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={proyectoInicial ? 'EDITAR PROYECTO' : 'NUEVO PROYECTO'}
    >
      <form className="proyecto-form" onSubmit={handleSubmit}>
        {error && <div className="proyecto-form__error">{error}</div>}

        <div className="proyecto-form__field">
          <label className="proyecto-form__label">NOMBRE DEL PROYECTO</label>
          <input
            id="input-nombre-proyecto"
            className="proyecto-form__input"
            type="text"
            placeholder="Mi diagrama de flujo..."
            value={nombre}
            onChange={e => setNombre(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="proyecto-form__field">
          <label className="proyecto-form__label">DESCRIPCIÓN (opcional)</label>
          <textarea
            id="input-desc-proyecto"
            className="proyecto-form__textarea"
            placeholder="Describe el propósito de este diagrama..."
            value={descripcion}
            onChange={e => setDescripcion(e.target.value)}
            rows={3}
          />
        </div>

        {!proyectoInicial && plantillas.length > 0 && (
          <div className="proyecto-form__field">
            <label className="proyecto-form__label" htmlFor="input-plantilla-proyecto">PLANTILLA (opcional)</label>
            <select
              id="input-plantilla-proyecto"
              className="proyecto-form__input plantilla-select"
              value={plantillaId}
              onChange={e => setPlantillaId(e.target.value)}
            >
              <option value="">Lienzo en blanco</option>
              <optgroup label="Plantillas base">
                {plantillas.filter(p => p.origen === 'base').map(p => (
                  <option key={p.id} value={p.id}>{p.nombre} · {p.clases} clases</option>
                ))}
              </optgroup>
              {plantillas.some(p => p.origen === 'usuario') && (
                <optgroup label="Mis plantillas">
                  {plantillas.filter(p => p.origen === 'usuario').map(p => (
                    <option key={p.id} value={p.id}>{p.nombre} · {p.clases} clases</option>
                  ))}
                </optgroup>
              )}
            </select>
            {plantillaId && (
              <div className="plantilla-select__ayuda">
                {plantillas.find(p => p.id === plantillaId)?.descripcion || 'El proyecto empezará con estas clases y relaciones.'}
              </div>
            )}
          </div>
        )}

        <div className="proyecto-form__actions">
          <button type="button" className="proyecto-form__btn-cancel" onClick={onClose}>
            CANCELAR
          </button>
          <button type="submit" className="proyecto-form__btn-submit" disabled={loading} id="btn-guardar-proyecto">
            {loading ? '...' : (proyectoInicial ? 'GUARDAR CAMBIOS' : 'CREAR PROYECTO')}
          </button>
        </div>
      </form>
    </Modal>
  );
};
