import React, { useCallback, useEffect, useState } from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import {
  EVENTO_GUARDAR_PLANTILLA,
  eliminarPlantilla,
  guardarPlantilla,
  listarPlantillas,
  type PlantillaMeta,
} from './plantillas';
import './plantillas.css';

/** CU42: "Guardar como plantilla" (se abre desde ARCHIVO del menú). Montado en la sala. */
export const GuardarPlantillaModal: React.FC<{ nombreProyecto?: string }> = ({ nombreProyecto }) => {
  const { getDiagramState } = useDiagram();
  const [abierto, setAbierto] = useState(false);
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [mias, setMias] = useState<PlantillaMeta[]>([]);
  const [estado, setEstado] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null);
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    try {
      setMias((await listarPlantillas()).filter(p => p.origen === 'usuario'));
    } catch { /* sin sesión: solo se puede guardar con sesión */ }
  }, []);

  useEffect(() => {
    const abrir = () => {
      setNombre(nombreProyecto ? `Plantilla ${nombreProyecto}` : '');
      setDescripcion('');
      setEstado(null);
      setAbierto(true);
      cargar();
    };
    window.addEventListener(EVENTO_GUARDAR_PLANTILLA, abrir);
    return () => window.removeEventListener(EVENTO_GUARDAR_PLANTILLA, abrir);
  }, [cargar, nombreProyecto]);

  useEffect(() => {
    if (!abierto) return;
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setAbierto(false); };
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [abierto]);

  if (!abierto) return null;

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    const { nodes, relations } = getDiagramState();
    setGuardando(true);
    setEstado(null);
    try {
      await guardarPlantilla(nombre.trim(), descripcion.trim(), { nodes, relations });
      setEstado({ tipo: 'ok', texto: `Plantilla guardada (${nodes.length} clases). Ya aparece al crear un proyecto nuevo.` });
      cargar();
    } catch (err) {
      setEstado({ tipo: 'error', texto: err instanceof Error ? err.message : 'No se pudo guardar la plantilla' });
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="plantilla-modal__fondo" onClick={() => setAbierto(false)}>
      <div className="plantilla-modal" role="dialog" aria-modal="true" aria-labelledby="plantilla-modal-titulo" onClick={e => e.stopPropagation()}>
        <h3 id="plantilla-modal-titulo">Guardar como plantilla</h3>
        <p className="plantilla-modal__nota">Se guarda el diagrama actual (clases y relaciones). Solo tú verás tus plantillas al crear proyectos.</p>
        <form onSubmit={guardar} className="plantilla-modal__form">
          <label>
            Nombre
            <input value={nombre} onChange={e => setNombre(e.target.value)} maxLength={120} required autoFocus />
          </label>
          <label>
            Descripción (opcional)
            <textarea value={descripcion} onChange={e => setDescripcion(e.target.value)} maxLength={500} rows={2} />
          </label>
          {estado && <div className={`plantilla-modal__estado plantilla-modal__estado--${estado.tipo}`} role="status">{estado.texto}</div>}
          <div className="plantilla-modal__acciones">
            <button type="button" onClick={() => setAbierto(false)}>Cerrar</button>
            <button type="submit" className="is-primario" disabled={guardando || !nombre.trim()}>
              {guardando ? 'Guardando…' : 'Guardar plantilla'}
            </button>
          </div>
        </form>
        {mias.length > 0 && (
          <div className="plantilla-modal__mias">
            <h4>Mis plantillas</h4>
            <ul>
              {mias.map(p => (
                <li key={p.id}>
                  <span>{p.nombre} <small>· {p.clases} clases</small></span>
                  <button type="button" onClick={async () => { await eliminarPlantilla(p.id).catch(() => {}); cargar(); }}>Borrar</button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
