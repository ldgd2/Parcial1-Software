import React, { useState } from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { X, ChevronRight, ChevronLeft, MessageSquarePlus, CheckCircle2 } from 'lucide-react';
import './PropertiesPanel.css';

function getCurrentUser() {
  const cached = localStorage.getItem('usuario_nombre');
  if (cached) return cached;
  
  try {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      let name = payload.nombre || payload.sub;
      if (typeof name === 'string' && name.includes('@')) {
        name = name.split('@')[0];
      }
      return name || 'Colaborador';
    }
  } catch (e) {}
  return localStorage.getItem('guestNickname') || 'Colaborador';
}

export const PropertiesPanel: React.FC = () => {
  const { nodes, relations, correcciones, selectedId, updateNode, updateRelation, setSelectedId, addCorreccion, resolveCorreccion } = useDiagram();
  const [isMinimized, setIsMinimized] = useState(false);
  const [newCorr, setNewCorr] = useState('');
  const [userName, setUserName] = useState(getCurrentUser());

  React.useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !localStorage.getItem('usuario_nombre')) {
      import('@/shared/lib/api').then(({ apiFetch }) => {
        apiFetch('/usuarios/me').then(user => {
          if (user && user.nombre) {
            localStorage.setItem('usuario_nombre', user.nombre);
            setUserName(user.nombre);
          }
        }).catch(() => {});
      });
    }
  }, []);

  if (!selectedId) return null;

  const selectedNode = nodes.find(n => n.id === selectedId);
  const selectedRel = relations.find(r => r.id === selectedId);

  if (!selectedNode && !selectedRel) return null;

  const isNode = !!selectedNode;
  const currentItemCorrecciones = correcciones[selectedId] || [];
  const abiertas = currentItemCorrecciones.filter(c => c.estado === 'abierta');
  const resueltas = currentItemCorrecciones.filter(c => c.estado === 'resuelta');

  const handleAddCorreccion = () => {
    if (!newCorr.trim()) return;
    addCorreccion(selectedId, newCorr.trim(), userName);
    setNewCorr('');
  };

  return (
    <div className={`properties-panel ${isMinimized ? 'properties-panel--minimized' : ''}`}>
      <div className="properties-panel__header">
        {!isMinimized && <h3>Propiedades {isNode ? 'de Clase' : 'de Relación'}</h3>}
        <div className="properties-panel__actions">
          <button className="properties-panel__btn" onClick={() => setIsMinimized(!isMinimized)} title={isMinimized ? "Expandir" : "Minimizar"}>
            {isMinimized ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
          </button>
          {!isMinimized && (
            <button className="properties-panel__btn" onClick={() => setSelectedId(null)} title="Cerrar">
              <X size={16} />
            </button>
          )}
        </div>
      </div>
      
      {!isMinimized && (
        <div className="properties-panel__content">
          <div className="properties-section">
            <h4 className="properties-section__title">General</h4>
            {isNode && selectedNode && (
              <>
                <div className="property-group">
                  <label>Nombre</label>
                  <input 
                    type="text" 
                    value={selectedNode.nombre} 
                    onChange={(e) => updateNode(selectedNode.id, { nombre: e.target.value })} 
                    placeholder="Nombre de la clase"
                  />
                </div>
                {selectedNode.type === 'class' && (
                  <div className="property-group">
                    <label>Estereotipo</label>
                    <input 
                      type="text" 
                      value={selectedNode.estereotipo || ''} 
                      onChange={(e) => updateNode(selectedNode.id, { estereotipo: e.target.value })} 
                      placeholder="ej. table"
                    />
                  </div>
                )}
                <div className="property-group">
                  <label>Color</label>
                  <input 
                    type="color" 
                    value={selectedNode.color} 
                    onChange={(e) => updateNode(selectedNode.id, { color: e.target.value })} 
                  />
                </div>
                {selectedNode.type === 'note' && (
                  <div className="property-group">
                    <label>Contenido</label>
                    <textarea 
                      value={selectedNode.contenido || ''} 
                      onChange={(e) => updateNode(selectedNode.id, { contenido: e.target.value })} 
                      rows={4}
                    />
                  </div>
                )}
              </>
            )}

            {!isNode && selectedRel && (
              <>
                <div className="property-group">
                  <label>Etiqueta Central</label>
                  <input 
                    type="text" 
                    value={selectedRel.label || ''} 
                    onChange={(e) => updateRelation(selectedRel.id, { label: e.target.value })} 
                    placeholder="Nombre de la relación"
                  />
                </div>
                <div className="property-group">
                  <label>Card. Origen</label>
                  <input 
                    type="text" 
                    value={selectedRel.sourceLabel || ''} 
                    onChange={(e) => updateRelation(selectedRel.id, { sourceLabel: e.target.value })} 
                    placeholder="ej. 1, 0..1"
                  />
                </div>
                <div className="property-group">
                  <label>Card. Destino</label>
                  <input 
                    type="text" 
                    value={selectedRel.targetLabel || ''} 
                    onChange={(e) => updateRelation(selectedRel.id, { targetLabel: e.target.value })} 
                    placeholder="ej. n, 0..m"
                  />
                </div>
              </>
            )}
          </div>

          <div className="properties-section">
            <h4 className="properties-section__title">Correcciones</h4>
            
            <div className="correcciones-list">
              {abiertas.map(c => (
                <div key={c.id} className="correccion-card correccion-card--abierta">
                  <div className="correccion-card__header">
                    <span className="correccion-card__autor">{c.autorNombre}</span>
                    <span className="correccion-card__fecha">{new Date(c.fecha).toLocaleDateString()}</span>
                  </div>
                  <p className="correccion-card__texto">{c.texto}</p>
                  <button className="correccion-card__resolve" onClick={() => resolveCorreccion(selectedId, c.id, userName)}>
                    <CheckCircle2 size={14} /> Solucionar
                  </button>
                </div>
              ))}
              {resueltas.map(c => (
                <div key={c.id} className="correccion-card correccion-card--resuelta">
                  <div className="correccion-card__header">
                    <span className="correccion-card__autor">{c.autorNombre}</span>
                    <span className="correccion-card__fecha">Resuelto por {c.resueltoPorNombre}</span>
                  </div>
                  <p className="correccion-card__texto">{c.texto}</p>
                </div>
              ))}
              {abiertas.length === 0 && resueltas.length === 0 && (
                <div className="correcciones-empty">No hay correcciones.</div>
              )}
            </div>

            <div className="correccion-input">
              <textarea 
                value={newCorr} 
                onChange={(e) => setNewCorr(e.target.value)} 
                placeholder="Añadir corrección/problema..."
                rows={2}
              />
              <button onClick={handleAddCorreccion} disabled={!newCorr.trim()}>
                <MessageSquarePlus size={16} /> Añadir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
