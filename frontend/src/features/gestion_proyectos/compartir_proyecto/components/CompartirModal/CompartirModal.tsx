import React, { useEffect, useState } from 'react';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import { proyectoService } from '@/features/gestion_proyectos/shared/utils/proyectoService';
import type { Miembro, Proyecto } from '@/features/gestion_proyectos/shared/utils/types';
import './CompartirModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  proyecto: Proyecto | null;
}

const EMAIL_VALIDO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const ETIQUETA_NIVEL: Record<Miembro['nivel'], string> = { anfitrion: 'Anfitrión', editor: 'Editor', lector: 'Lector' };

export const CompartirModal: React.FC<Props> = ({ isOpen, onClose, proyecto }) => {
  const [copiado, setCopiado] = useState(false);
  const [email, setEmail] = useState('');
  const [permiso, setPermiso] = useState<'edit' | 'view'>('edit');
  const [enviando, setEnviando] = useState(false);
  const [aviso, setAviso] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null);
  const [miembros, setMiembros] = useState<Miembro[]>([]);

  const cargarMiembros = async (id: number) => {
    try { setMiembros(await proyectoService.miembros(id)); } catch { setMiembros([]); }
  };

  useEffect(() => {
    if (isOpen && proyecto) {
      setEmail(''); setPermiso('edit'); setAviso(null);
      cargarMiembros(proyecto.id);
    }
  }, [isOpen, proyecto?.id]);

  if (!proyecto) return null;
  const link = proyectoService.getLinkInvitacion(proyecto.codigo_acceso);

  const copiar = async () => {
    await navigator.clipboard.writeText(link);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  // CU08: invitar a un usuario registrado por su correo, con el permiso elegido
  const invitar = async (e: React.FormEvent) => {
    e.preventDefault();
    const correo = email.trim();
    if (!EMAIL_VALIDO.test(correo)) {
      setAviso({ tipo: 'error', texto: 'Ingresa un correo electrónico válido.' });
      return;
    }
    setEnviando(true); setAviso(null);
    try {
      const m = await proyectoService.invitar(proyecto.id, correo, permiso);
      setAviso({ tipo: 'ok', texto: `${m.nombre} se agregó como ${ETIQUETA_NIVEL[m.nivel].toLowerCase()}. Lo verá en “Compartidos conmigo”.` });
      setEmail('');
      await cargarMiembros(proyecto.id);
    } catch (err: any) {
      setAviso({ tipo: 'error', texto: err.message || 'No se pudo compartir el proyecto.' });
    } finally {
      setEnviando(false);
    }
  };

  const cambiar = async (m: Miembro, nuevo: 'edit' | 'view') => {
    try {
      await proyectoService.cambiarPermiso(proyecto.id, m.usuario_id, nuevo);
      await cargarMiembros(proyecto.id);
    } catch (err: any) {
      setAviso({ tipo: 'error', texto: err.message || 'No se pudo cambiar el permiso.' });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="COMPARTIR PROYECTO" width="560px">
      <div className="compartir-modal">
        <div className="compartir-modal__proyecto-name">
          <span className="compartir-modal__icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
          {proyecto.nombre}
        </div>

        <form className="compartir-modal__invitar" onSubmit={invitar}>
          <label className="compartir-modal__label" htmlFor="input-email-invitado">Invitar por correo</label>
          <div className="compartir-modal__fila">
            <input
              id="input-email-invitado"
              className="compartir-modal__email"
              type="email"
              placeholder="correo@ejemplo.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="off"
            />
            <select
              id="select-permiso-invitado"
              className="compartir-modal__permiso"
              value={permiso}
              onChange={e => setPermiso(e.target.value as 'edit' | 'view')}
              aria-label="Permiso"
            >
              <option value="edit">Editor</option>
              <option value="view">Lector</option>
            </select>
            <button id="btn-invitar" type="submit" className="compartir-modal__copy-btn" disabled={enviando || !email.trim()}>
              {enviando ? '...' : 'INVITAR'}
            </button>
          </div>
          {aviso && (
            <div role="status" className={`compartir-modal__aviso compartir-modal__aviso--${aviso.tipo}`}>{aviso.texto}</div>
          )}
        </form>

        {miembros.length > 0 && (
          <div className="compartir-modal__miembros">
            <div className="compartir-modal__label">Miembros</div>
            {miembros.map(m => (
              <div key={m.usuario_id} className="compartir-modal__miembro">
                <div className="compartir-modal__miembro-datos">
                  <span className="compartir-modal__miembro-nombre">{m.nombre}</span>
                  {m.email && <span className="compartir-modal__miembro-email">{m.email}</span>}
                </div>
                {m.nivel === 'anfitrion' ? (
                  <span className="compartir-modal__miembro-rol">Anfitrión</span>
                ) : (
                  <select
                    className="compartir-modal__permiso"
                    value={m.permiso}
                    onChange={e => cambiar(m, e.target.value as 'edit' | 'view')}
                    aria-label={`Permiso de ${m.nombre}`}
                  >
                    <option value="edit">Editor</option>
                    <option value="view">Lector</option>
                  </select>
                )}
              </div>
            ))}
          </div>
        )}

        <div>
          <div className="compartir-modal__label">O comparte el enlace</div>
          <div className="compartir-modal__link-box">
            <input
              id="input-link-invitacion"
              className="compartir-modal__link-input"
              type="text"
              value={link}
              readOnly
              onClick={e => (e.target as HTMLInputElement).select()}
            />
            <button
              id="btn-copiar-link"
              className={`compartir-modal__copy-btn ${copiado ? 'compartir-modal__copy-btn--copiado' : ''}`}
              onClick={copiar}
            >
              {copiado ? <><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight:4}}><polyline points="20 6 9 17 4 12"/></svg> COPIADO</> : 'COPIAR'}
            </button>
          </div>
          <div className="compartir-modal__info">
            <span className="compartir-modal__info-icon"><svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l10 10-10 10L2 12 12 2z"/></svg></span>
            Con el enlace, la persona solicita unirse y tú la apruebas desde la sala.
          </div>
        </div>
      </div>
    </Modal>
  );
};
