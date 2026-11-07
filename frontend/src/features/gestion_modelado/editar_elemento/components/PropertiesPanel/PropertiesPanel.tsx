import React, { useState } from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { useRealTimeSync, getUserIdentity } from '@/features/gestion_concurrencia/sincronizacion_tiempo_real/context/RealTimeSyncContext';
import { X, ChevronRight, ChevronLeft, MessageSquarePlus, CheckCircle2, Lock } from 'lucide-react';
import './PropertiesPanel.css';

function getCurrentUser() {
  const cached = localStorage.getItem('usuario_nombre');
  if (cached) return cached;
  
  import('@/shared/lib/TokenService').then(({ TokenService }) => {
    try {
      const token = TokenService.getToken();
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        let name = payload.nombre || payload.sub;
        if (typeof name === 'string' && name.includes('@')) {
          name = name.split('@')[0];
        }
        localStorage.setItem('usuario_nombre', name || 'Colaborador');
      }
    } catch (e) {}
  });

  return localStorage.getItem('guestNickname') || 'Colaborador';
}

export const PropertiesPanel: React.FC = () => {
  const { nodes, relations, correcciones, selectedIds, updateNode, updateRelation, setSelectedIds, addCorreccion, resolveCorreccion } = useDiagram();
  const selectedId = selectedIds.length === 1 ? selectedIds[0] : null;
  const realTimeSync = useRealTimeSync();
  const lockElement = realTimeSync?.lockElement;
  const refreshLock = realTimeSync?.refreshLock;
  const unlockElement = realTimeSync?.unlockElement;
  const lockedElements = realTimeSync?.lockedElements || {};

  const [isMinimized, setIsMinimized] = useState(false);
  const [newCorr, setNewCorr] = useState('');
  const [userName, setUserName] = useState(getCurrentUser());
  const [newHabilidad, setNewHabilidad] = useState('');

  const handleFocus = (subId: string) => {
    if (lockElement && selectedId) lockElement(`${selectedId}:${subId}`);
  };

  const handleBlur = (subId: string) => {
    if (unlockElement && selectedId) unlockElement(`${selectedId}:${subId}`);
  };

  const handleChangeLock = (subId: string) => {
    if (refreshLock && selectedId) refreshLock(`${selectedId}:${subId}`);
  };

  const lockedBy = (subId: string) => { return lockedElements[`${selectedId}:${subId}`]; };
  const isLocked = (subId: string) => {
    if (!selectedId) return false;
    const lock = lockedElements[`${selectedId}:${subId}`];
    return lock !== undefined;
  };

  React.useEffect(() => {
    import('@/shared/lib/TokenService').then(({ TokenService }) => {
      const token = TokenService.getToken();
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
    });
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

  const handleAddHabilidad = (customTag?: string) => {
    if (!selectedNode) return;
    const tagToAdd = customTag || newHabilidad;
    if (!tagToAdd.trim()) return;
    const current = selectedNode.responsabilidades || [];
    const newItems = tagToAdd
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0 && !current.includes(s));
    if (newItems.length > 0) {
      updateNode(selectedNode.id, { responsabilidades: [...current, ...newItems] });
    }
    if (!customTag) {
      setNewHabilidad('');
    }
  };

  return (
    <div className={`properties-panel ${isMinimized ? 'properties-panel--minimized' : ''}`}>
      <div className="properties-panel__header">
        {!isMinimized && <h3>Propiedades {isNode ? 'de Clase' : 'de Relacin'}</h3>}
        <div className="properties-panel__actions">
          <button className="properties-panel__btn" onClick={() => setIsMinimized(!isMinimized)} title={isMinimized ? "Expandir" : "Minimizar"}>
            {isMinimized ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
          </button>
          {!isMinimized && (
            <button className="properties-panel__btn" onClick={() => setSelectedIds([])} title="Cerrar">
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
                  <label>Nombre {isLocked('nombre') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                  <input 
                    type="text" 
                    value={selectedNode.nombre} 
                    onChange={(e) => { updateNode(selectedNode.id, { nombre: e.target.value }); handleChangeLock('nombre'); }} 
                    onFocus={() => handleFocus('nombre')}
                    onBlur={() => handleBlur('nombre')}
                    placeholder="Nombre de la clase"
                    disabled={isLocked('nombre')}
                  />
                </div>
                {selectedNode.type === 'class' && (
                  <div className="property-group">
                    <label>Estereotipo {isLocked('estereotipo') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                    <input 
                      type="text" 
                      value={selectedNode.estereotipo || ''} 
                      onChange={(e) => { updateNode(selectedNode.id, { estereotipo: e.target.value }); handleChangeLock('estereotipo'); }} 
                      onFocus={() => handleFocus('estereotipo')}
                      onBlur={() => handleBlur('estereotipo')}
                      placeholder="ej. table"
                      disabled={isLocked('estereotipo')}
                    />
                  </div>
                )}
                <div className="property-group">
                  <label>Color {isLocked('color') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                  <input 
                    type="color" 
                    value={selectedNode.color} 
                    onChange={(e) => { updateNode(selectedNode.id, { color: e.target.value }); handleChangeLock('color'); }}
                    onFocus={() => handleFocus('color')}
                    onBlur={() => handleBlur('color')}
                    disabled={isLocked('color')}
                  />
                </div>
                {selectedNode.type === 'note' && (
                  <div className="property-group">
                    <label>Contenido {isLocked('contenido') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                    <textarea 
                      value={selectedNode.contenido || ''} 
                      onChange={(e) => { updateNode(selectedNode.id, { contenido: e.target.value }); handleChangeLock('contenido'); }} 
                      onFocus={() => handleFocus('contenido')}
                      onBlur={() => handleBlur('contenido')}
                      rows={4}
                      disabled={isLocked('contenido')}
                    />
                  </div>
                )}

                {/* Asignación de Responsable y Habilidades / Responsabilidades */}
                {selectedNode.type !== 'note' && (
                  <>
                    <div className="property-group">
                      <label>Responsable de Clase</label>
                      <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                        <input
                          type="text"
                          value={selectedNode.responsable || ''}
                          onChange={(e) => updateNode(selectedNode.id, { responsable: e.target.value })}
                          placeholder="ej. Juan, Dev1..."
                          style={{ flex: 1 }}
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const currentId = getUserIdentity();
                            const myName = userName || currentId.nickname || 'Colaborador';
                            updateNode(selectedNode.id, { responsable: myName });
                          }}
                          title="Asignarme a mí como responsable"
                          style={{
                            background: 'var(--primary)',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '0 8px',
                            fontSize: '11px',
                            cursor: 'pointer',
                            fontWeight: 600,
                            whiteSpace: 'nowrap'
                          }}
                        >
                          Asignarme
                        </button>
                      </div>
                      {/* Colaboradores de la sala para asignación rápida */}
                      {realTimeSync?.roomUsers && realTimeSync.roomUsers.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '4px' }}>
                          {realTimeSync.roomUsers.map((u: any, idx: number) => {
                            const uName = u.nickname || u.nombre || `Colab ${idx + 1}`;
                            const isCurrentResp = selectedNode.responsable === uName;
                            return (
                              <button
                                key={idx}
                                type="button"
                                onClick={() => updateNode(selectedNode.id, { responsable: uName })}
                                style={{
                                  background: isCurrentResp ? 'var(--primary)' : 'rgba(255,255,255,0.06)',
                                  border: '1px solid ' + (isCurrentResp ? 'var(--primary)' : 'var(--border-color)'),
                                  color: isCurrentResp ? '#fff' : 'var(--text-secondary)',
                                  borderRadius: '10px',
                                  padding: '1px 7px',
                                  fontSize: '10px',
                                  cursor: 'pointer',
                                  fontWeight: isCurrentResp ? 700 : 400
                                }}
                              >
                                {uName}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    <div className="property-group">
                      <label>Habilidades / Responsabilidades</label>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '6px' }}>
                        {(selectedNode.responsabilidades || []).map((resp, idx) => (
                          <span
                            key={idx}
                            style={{
                              background: 'rgba(255,255,255,0.08)',
                              border: '1px solid var(--border-color)',
                              borderRadius: '12px',
                              padding: '2px 8px',
                              fontSize: '11px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            {resp}
                            <button
                              type="button"
                              onClick={() => {
                                const updated = (selectedNode.responsabilidades || []).filter((_, i) => i !== idx);
                                updateNode(selectedNode.id, { responsabilidades: updated });
                              }}
                              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: 0, fontSize: '12px', lineHeight: 1 }}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                        <input
                          type="text"
                          value={newHabilidad}
                          onChange={(e) => setNewHabilidad(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleAddHabilidad();
                            }
                          }}
                          placeholder="backend, auth, validación..."
                          style={{ flex: 1 }}
                        />
                        <button
                          type="button"
                          onClick={() => handleAddHabilidad()}
                          disabled={!newHabilidad.trim()}
                          style={{
                            background: 'var(--surface-color)',
                            border: '1px solid var(--border-color)',
                            color: 'var(--text-primary)',
                            borderRadius: '4px',
                            padding: '0 10px',
                            cursor: 'pointer',
                            fontWeight: 700
                          }}
                        >
                          +
                        </button>
                      </div>
                      {/* Sugerencias rápidas */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {['Backend', 'Frontend', 'Database', 'Seguridad', 'API'].map(sug => {
                          const already = (selectedNode.responsabilidades || []).includes(sug);
                          return (
                            <button
                              key={sug}
                              type="button"
                              onClick={() => handleAddHabilidad(sug)}
                              disabled={already}
                              style={{
                                background: already ? 'transparent' : 'rgba(37,211,102,0.1)',
                                border: '1px dashed ' + (already ? 'var(--border-color)' : '#25D366'),
                                color: already ? 'var(--text-secondary)' : '#25D366',
                                borderRadius: '10px',
                                padding: '1px 6px',
                                fontSize: '10px',
                                cursor: already ? 'default' : 'pointer'
                              }}
                            >
                              + {sug}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </>
                )}
              </>
            )}

            {!isNode && selectedRel && (
              <>
                <div className="property-group">
                  <label>Etiqueta Central {isLocked('label') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                  <input 
                    type="text" 
                    value={selectedRel.label || ''} 
                    onChange={(e) => { updateRelation(selectedRel.id, { label: e.target.value }); handleChangeLock('label'); }} 
                    onFocus={() => handleFocus('label')}
                    onBlur={() => handleBlur('label')}
                    placeholder="Nombre de la relacin"
                    disabled={isLocked('label')}
                  />
                </div>
                <div className="property-group">
                  <label>Card. Origen {isLocked('sourceLabel') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                  <input 
                    type="text" 
                    value={selectedRel.sourceLabel || ''} 
                    onChange={(e) => { updateRelation(selectedRel.id, { sourceLabel: e.target.value }); handleChangeLock('sourceLabel'); }} 
                    onFocus={() => handleFocus('sourceLabel')}
                    onBlur={() => handleBlur('sourceLabel')}
                    placeholder="ej. 1, 0..1"
                    disabled={isLocked('sourceLabel')}
                  />
                </div>
                <div className="property-group">
                  <label>Card. Destino {isLocked('targetLabel') && <span title={lockedBy('')}><Lock size={12} style={{ marginLeft: 4, verticalAlign: 'middle' }} /></span>}</label>
                  <input 
                    type="text" 
                    value={selectedRel.targetLabel || ''} 
                    onChange={(e) => { updateRelation(selectedRel.id, { targetLabel: e.target.value }); handleChangeLock('targetLabel'); }} 
                    onFocus={() => handleFocus('targetLabel')}
                    onBlur={() => handleBlur('targetLabel')}
                    placeholder="ej. n, 0..m"
                    disabled={isLocked('targetLabel')}
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
