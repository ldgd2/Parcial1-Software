import React, { useRef, useState, useCallback, useEffect } from 'react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { ClassNode as ClassNodeComponent } from '@/features/gestion_modelado/editar_elemento/components/ClassNode/ClassNode';
import { RelationLayer } from '@/features/gestion_modelado/conectar_elemento/components/RelationLayer/RelationLayer';
import { ConnectPicker } from '@/features/gestion_modelado/conectar_elemento/components/ConnectPicker/ConnectPicker';
import { ContextMenu, type ContextMenuOption } from '@/features/gestion_modelado/lienzo_principal/components/ContextMenu/ContextMenu';
import type { RelationType } from '@/features/gestion_modelado/shared/types/types';
import './DiagramCanvas.css';

interface Props {
  onCanvasClick: () => void;
}

export const DiagramCanvas: React.FC<Props> = ({ onCanvasClick }) => {
  const { nodes, addNode, updateNode, deleteNode, moveNode, selectedIds, setSelectedIds, connectingSource, activeTool, setActiveTool, startConnect, finishConnect, cancelConnect } = useDiagram();
  const canvasRef = useRef<HTMLDivElement>(null);

  // Pan & zoom
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const isPanning = useRef(false);
  const lastMouse = useRef({ x: 0, y: 0 });

  // Multi-Drag
  const dragging = useRef<{ items: { id: string; startX: number; startY: number; nodeX: number; nodeY: number }[] } | null>(null);

  // Marquee Selection
  const [marquee, setMarquee] = useState<{ startX: number, startY: number, endX: number, endY: number } | null>(null);

  // CU9: picker de tipo de relación
  const [picker, setPicker] = useState<{ x: number; y: number; targetId: string } | null>(null);

  // Context Menu
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; targetId?: string } | null>(null);

  // Calcular posiciones de nodos para colisiones y RelationLayer
  const nodePositions = nodes.map(n => {
    let height = 160;
    if (n.type === 'note') {
      height = 90;
    } else if (n.type === 'enum') {
      height = 45 + (n.valores?.length || 0) * 28 + 20;
    } else {
      height = 45 + (n.atributos.length * 28) + 20 + (n.metodos.length * 28) + 20;
    }
    return {
      id: n.id,
      x: n.x,
      y: n.y,
      width: n.width || 220,
      height,
    };
  });

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // Si clickea con click central, iniciamos paneo
    if (e.button === 1) {
      e.preventDefault();
      isPanning.current = true;
      lastMouse.current = { x: e.clientX, y: e.clientY };
      return;
    }

    // Click izquierdo en el fondo = Iniciar Marquee
    if (e.button === 0 && (e.target === canvasRef.current || (e.target as HTMLElement).classList.contains('diagram-canvas__inner') || (e.target as HTMLElement).classList.contains('diagram-canvas__grid'))) {
      if (connectingSource) {
        cancelConnect();
      } else {
        if (!e.ctrlKey) {
          setSelectedIds([]);
        }
        onCanvasClick();
        
        // Coordenadas locales respecto al canvas (considerando pan y zoom)
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
          const localX = (e.clientX - rect.left - pan.x) / zoom;
          const localY = (e.clientY - rect.top - pan.y) / zoom;
          setMarquee({ startX: localX, startY: localY, endX: localX, endY: localY });
        }
      }
    }
  }, [pan, zoom, connectingSource, cancelConnect, setSelectedIds, onCanvasClick]);

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    if (e.ctrlKey) {
      // Ctrl + Wheel = Pan Horizontal
      setPan(p => ({ x: p.x - e.deltaY * 2, y: p.y }));
    } else if (e.shiftKey) {
      // Shift + Wheel = Pan Vertical
      setPan(p => ({ x: p.x, y: p.y - e.deltaY * 2 }));
    } else {
      // Wheel sola = Zoom (o podría ser pan y Ctrl = zoom, pero mantendremos wheel=zoom, shift/ctrl=pan)
      // Ajustaremos zoom si e.deltaY != 0, o podemos hacer que wheel solo panee
      // El usuario pidió "utilizar control con la ruta de mouse para moverme horizontalmente, shift rueda raton para verticalmente"
      // Asumiremos que rueda normal = zoom
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom(z => Math.min(3, Math.max(0.2, z * delta)));
    }
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('wheel', handleWheel, { passive: false });
    }
    return () => { if (canvas) canvas.removeEventListener('wheel', handleWheel); };
  }, [handleWheel]);

  const startNodeDrag = useCallback((id: string, e: React.MouseEvent, _nodeX: number, _nodeY: number) => {
    if (connectingSource) return; // en modo conexión no arrastrar
    e.stopPropagation();
    
    let draggingIds = selectedIds;
    if (!selectedIds.includes(id)) {
      if (e.ctrlKey) {
        draggingIds = [...selectedIds, id];
        setSelectedIds(draggingIds);
      } else {
        draggingIds = [id];
        setSelectedIds(draggingIds);
      }
    }
    
    const items = draggingIds.map(dId => {
      const n = nodes.find(nd => nd.id === dId);
      return {
        id: dId,
        startX: e.clientX,
        startY: e.clientY,
        nodeX: n?.x || 0,
        nodeY: n?.y || 0
      };
    });

    dragging.current = { items };
  }, [setSelectedIds, selectedIds, nodes, connectingSource]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragging.current) {
      const dx = (e.clientX - dragging.current.items[0].startX) / zoom;
      const dy = (e.clientY - dragging.current.items[0].startY) / zoom;
      
      // Update all selected nodes temporarily
      dragging.current.items.forEach(item => {
        moveNode(item.id, item.nodeX + dx, item.nodeY + dy);
      });
    }

    if (isPanning.current) {
      const dx = e.clientX - lastMouse.current.x;
      const dy = e.clientY - lastMouse.current.y;
      setPan(p => ({ x: p.x + dx, y: p.y + dy }));
      lastMouse.current = { x: e.clientX, y: e.clientY };
    }

    if (marquee) {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        const localX = (e.clientX - rect.left - pan.x) / zoom;
        const localY = (e.clientY - rect.top - pan.y) / zoom;
        setMarquee(prev => prev ? { ...prev, endX: localX, endY: localY } : null);

        // Calculate intersection
        const mX = Math.min(marquee.startX, localX);
        const mY = Math.min(marquee.startY, localY);
        const mW = Math.abs(marquee.startX - localX);
        const mH = Math.abs(marquee.startY - localY);

        const newSelected = nodePositions.filter(np => {
          const overlap = !(np.x > mX + mW || 
                            np.x + np.width < mX || 
                            np.y > mY + mH ||
                            np.y + np.height < mY);
          return overlap;
        }).map(np => np.id);

        setSelectedIds(newSelected);
      }
    }
  }, [zoom, moveNode, pan, marquee, nodePositions, setSelectedIds]);

  const handleMouseUp = useCallback(() => {
    if (dragging.current) {
      dragging.current.items.forEach(item => {
        const draggedNode = nodes.find(n => n.id === item.id);
        if (draggedNode && draggedNode.type === 'port') {
          const parts = nodes.filter(n => n.type === 'part');
          const cx = draggedNode.x + (draggedNode.width || 40) / 2;
          const cy = draggedNode.y + (draggedNode.height || 40) / 2;
          
          let overPart = false;
          for (const part of parts) {
            const pX = part.x;
            const pY = part.y;
            const pW = part.width || 120;
            const pH = part.height || 100;
            if (cx >= pX && cx <= pX + pW && cy >= pY && cy <= pY + pH) {
              overPart = true;
              break;
            }
          }
          if (!overPart) {
            alert('Un Port debe colocarse dentro de un Part.');
            deleteNode(draggedNode.id);
          }
        }
      });
    }

    dragging.current = null;
    isPanning.current = false;
    setMarquee(null);
    if (canvasRef.current) canvasRef.current.style.cursor = 'default';
  }, [nodes, deleteNode]);

  const handleNodeClick = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    const relationTools = ['association', 'inheritance', 'composition', 'aggregation', 'dependency', 'realization', 'directed', 'association_class', 'template_binding', 'instantiate', 'substitution', 'usage', 'trace', 'information_flow', 'abstraction', 'calls', 'delegate', 'assembly'];
    const isRelationTool = relationTools.includes(activeTool);

    if (activeTool === 'connect' || isRelationTool) {
      if (!connectingSource) {
        startConnect(id);
      } else {
        if (connectingSource === id) {
          if (isRelationTool && !['delegate', 'assembly', 'connector', 'association'].includes(activeTool)) {
            cancelConnect();
          } else if (activeTool === 'connect') {
            setPicker({ x: e.clientX, y: e.clientY, targetId: id });
          } else {
            finishConnect(id, activeTool as RelationType);
            setActiveTool('select');
          }
        } else {
          if (isRelationTool) {
            finishConnect(id, activeTool as RelationType);
            setActiveTool('select');
          } else {
            setPicker({ x: e.clientX, y: e.clientY, targetId: id });
          }
        }
      }
    } else {
      if (e.ctrlKey) {
        setSelectedIds(selectedIds.includes(id) ? selectedIds.filter(p => p !== id) : [...selectedIds, id]);
      } else {
        setSelectedIds([id]);
      }
    }
  }, [activeTool, connectingSource, startConnect, cancelConnect, setSelectedIds, selectedIds, finishConnect, setActiveTool]);

  const handlePickerSelect = useCallback((type: RelationType) => {
    if (picker) {
      finishConnect(picker.targetId, type);
      setPicker(null);
    }
  }, [picker, finishConnect]);

  const handleContextMenu = useCallback((e: React.MouseEvent, id?: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (id && !selectedIds.includes(id)) {
        setSelectedIds([id]);
    }
    setCtxMenu({ x: e.clientX, y: e.clientY, targetId: id });
  }, [selectedIds, setSelectedIds]);

  const getContextMenuOptions = (): ContextMenuOption[] => {
    if (ctxMenu?.targetId) {
      const node = nodes.find(n => n.id === ctxMenu.targetId);
      if (!node) return [];
      
      const isTable = (node as any).estereotipo === 'table';
      
      return [
        {
          label: 'Duplicar Selección',
          icon: <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
          action: () => {
            selectedIds.forEach(sId => {
              const nd = nodes.find(n => n.id === sId);
              if (nd) addNode(nd.type, { ...nd, id: undefined, x: nd.x + 40, y: nd.y + 40, nombre: `${nd.nombre}_copy` } as any);
            });
          }
        },
        {
          label: selectedIds.length > 1 ? 'Convertir Selección a Tablas' : (isTable ? 'Convertir a Clase' : 'Convertir a Tabla'),
          icon: <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16v16H4z"/><path d="M4 10h16M10 4v16"/></svg>,
          action: () => {
            selectedIds.forEach(sId => {
              const nd = nodes.find(n => n.id === sId);
              if (nd) updateNode(nd.id, { estereotipo: nd.estereotipo === 'table' ? undefined : 'table' } as any);
            });
          }
        },
        { separator: true, action: () => {} },
        {
          label: 'Eliminar Selección',
          danger: true,
          icon: <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
          action: () => {
             selectedIds.forEach(sId => deleteNode(sId));
             setSelectedIds([]);
          }
        }
      ];
    } else {
      return [
        { label: 'Nueva Clase', action: () => addNode('class') },
        { label: 'Nueva Interfaz', action: () => addNode('interface') },
        { label: 'Nueva Tabla (BD)', action: () => { addNode('class'); } },
        { separator: true, action: () => {} },
        { label: 'Nueva Nota', action: () => addNode('note') }
      ];
    }
  };

  return (
    <div
      className={`diagram-canvas${connectingSource ? ' diagram-canvas--connecting' : ''}`}
      ref={canvasRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onContextMenu={(e) => handleContextMenu(e)}
    >
      <div
        className="diagram-canvas__grid"
        style={{
          backgroundPosition: `${pan.x % (20 * zoom)}px ${pan.y % (20 * zoom)}px`,
          backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
        }}
      />

      <div
        className="diagram-canvas__inner"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
        }}
      >
        <RelationLayer nodePositions={nodePositions} />

        {nodes.map(node => (
          <div key={node.id} onContextMenu={(e) => handleContextMenu(e, node.id)}>
            <ClassNodeComponent
              node={node}
              onDragStart={(e) => startNodeDrag(node.id, e, node.x, node.y)}
              onNodeClick={(e) => handleNodeClick(node.id, e)}
              isConnectingMode={!!connectingSource}
              isConnectingSource={connectingSource === node.id}
            />
          </div>
        ))}
        
        {/* Marquee Rectangle */}
        {marquee && (
          <div style={{
             position: 'absolute',
             border: '1px solid rgba(0, 120, 215, 0.5)',
             backgroundColor: 'rgba(0, 120, 215, 0.1)',
             pointerEvents: 'none',
             left: Math.min(marquee.startX, marquee.endX),
             top: Math.min(marquee.startY, marquee.endY),
             width: Math.abs(marquee.startX - marquee.endX),
             height: Math.abs(marquee.startY - marquee.endY),
             zIndex: 9999
          }} />
        )}
      </div>

      <div className="diagram-canvas__zoom-badge">
        {Math.round(zoom * 100)}%
      </div>

      {picker && (
        <ConnectPicker
          x={picker.x}
          y={picker.y}
          onPick={handlePickerSelect}
          onCancel={() => { setPicker(null); cancelConnect(); }}
        />
      )}

      {ctxMenu && (
        <ContextMenu
          x={ctxMenu.x}
          y={ctxMenu.y}
          options={getContextMenuOptions()}
          onClose={() => setCtxMenu(null)}
        />
      )}
    </div>
  );
};
