import React, { useState } from 'react';
import { Modal } from '@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal';
import type { ComentarioElemento } from '../types';
import './CommentThreadModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  elementName: string;
  elementoId: string;
  elementoTipo: 'node' | 'relation';
  comentarios: ComentarioElemento[];
  onAgregar: (texto: string) => Promise<any>;
  onCambiarEstado: (id: string, nuevoEstado: 'abierto' | 'resuelto') => Promise<any>;
  onEliminar: (id: string) => Promise<any>;
}

const formatFecha = (iso: string) => {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

export const CommentThreadModal: React.FC<Props> = ({
  isOpen,
  onClose,
  elementName,
  elementoTipo,
  comentarios,
  onAgregar,
  onCambiarEstado,
  onEliminar
}) => {
  const [nuevoTexto, setNuevoTexto] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');

  const abiertos = comentarios.filter(c => c.estado === 'abierto').length;

  const enviar = async () => {
    if (!nuevoTexto.trim() || enviando) return;
    setEnviando(true);
    setError('');
    try {
      await onAgregar(nuevoTexto.trim());
      setNuevoTexto('');
    } catch (err: any) {
      setError(err?.message || 'No se pudo publicar el comentario.');
    } finally {
      setEnviando(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    enviar();
  };

  // Enter publica; Shift+Enter hace salto de línea
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Comentarios" width="520px">
      <div className="comment-thread">
        <div className="comment-thread__meta">
          <div className="comment-thread__element">
            <span className="comment-thread__label">
              {elementoTipo === 'relation' ? 'RELACIÓN' : 'ELEMENTO'}
            </span>
            <span className="comment-thread__name" title={elementName}>{elementName}</span>
          </div>
          <span className={`comment-thread__summary${abiertos > 0 ? ' is-open' : ''}`}>
            {abiertos > 0 ? `${abiertos} ABIERTO${abiertos > 1 ? 'S' : ''}` : 'SIN PENDIENTES'}
          </span>
        </div>

        <div className="comment-thread__list">
          {comentarios.length === 0 ? (
            <div className="comment-thread__empty">
              No hay comentarios aún. Deja una nota técnica o feedback abajo.
            </div>
          ) : (
            comentarios.map(c => {
              const abierto = c.estado === 'abierto';
              return (
                <article key={c.id} className={`comment-item${abierto ? '' : ' comment-item--resuelto'}`}>
                  <header className="comment-item__head">
                    <div className="comment-item__who">
                      <span className="comment-item__author">{c.autor_nombre}</span>
                      {c.created_at && <span className="comment-item__date">{formatFecha(c.created_at)}</span>}
                    </div>
                    <span className={`comment-item__status${abierto ? ' is-open' : ''}`}>
                      {abierto ? 'ABIERTO' : 'RESUELTO'}
                    </span>
                  </header>

                  <p className="comment-item__text">{c.texto}</p>

                  <footer className="comment-item__actions">
                    <button
                      type="button"
                      className="comment-item__btn"
                      onClick={() => onCambiarEstado(c.id, abierto ? 'resuelto' : 'abierto')}
                    >
                      {abierto ? 'RESOLVER' : 'REABRIR'}
                    </button>
                    <button
                      type="button"
                      className="comment-item__btn comment-item__btn--danger"
                      onClick={() => onEliminar(c.id)}
                      aria-label={`Eliminar comentario de ${c.autor_nombre}`}
                    >
                      ELIMINAR
                    </button>
                  </footer>
                </article>
              );
            })
          )}
        </div>

        <form className="comment-thread__form" onSubmit={handleSubmit}>
          <label className="comment-thread__label" htmlFor="comment-thread-input">NUEVO COMENTARIO</label>
          <textarea
            id="comment-thread-input"
            className="comment-thread__input"
            value={nuevoTexto}
            onChange={e => setNuevoTexto(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe una nota técnica o feedback…"
            rows={2}
          />
          {error && <div className="comment-thread__error">{error}</div>}
          <div className="comment-thread__actions">
            <span className="comment-thread__hint">Enter para publicar · Shift+Enter nueva línea</span>
            <button
              type="submit"
              className="comment-thread__submit"
              disabled={enviando || !nuevoTexto.trim()}
            >
              {enviando ? 'PUBLICANDO…' : 'COMENTAR'}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
