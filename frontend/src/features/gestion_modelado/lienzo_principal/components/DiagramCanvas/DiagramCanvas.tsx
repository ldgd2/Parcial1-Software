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
  const { nodes, addNode, updateNode, deleteNode, moveNode, setSelectedId, connectingSource, activeTool, startConnect, finishConnect, cancelConnect } = useDiagram();
  const canvasRef = useRef<HTMLDivElement>(null);

  // Pan & zoom
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const isPanning = useRef(false);
  const lastMouse = useRef({ x: 0, y: 0 });

  // Drag
  const dragging = useRef<{ id: string; startX: number; startY: number; nodeX: number; nodeY: number } | null>(null);

  // CU9: picker de tipo de relación
  const [picker, setPicker] = useState<{ x: number; y: number; targetId: string } | null>(null);

  // Context Menu
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; targetId?: string } | null>(null);

  // Posiciones de nodos para RelationLayer (en coordenadas del canvas)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 1 && e.button !== 2) return;
    e.preventDefault();
    isPanning.current = true;
    lastMouse.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    if (e.ctrlKey) {
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom(z => Math.min(3, Math.max(0.2, z * delta)));
    } else {
      setPan(p => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }));
    }
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('wheel', handleWheel, { passive: false });
    }
    return () => { if (canvas) canvas.removeEventListener('wheel', handleWheel); };
  }, [handleWheel]);

  const startNodeDrag = useCallback((id: string, e: React.MouseEvent, nodeX: number, nodeY: number) => {
    if (connectingSource) return; // en modo conexión no arrastrar
    e.stopPropagation();
    setSelectedId(id);
    dragging.current = { id, startX: e.clientX, startY: e.clientY, nodeX, nodeY };
  }, [setSelectedId, connectingSource]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragging.current) {
      const dx = (e.clientX - dragging.current.startX) / zoom;
      const dy = (e.clientY - dragging.current.startY) / zoom;
      moveNode(dragging.current.id, dragging.current.nodeX + dx, dragging.current.nodeY + dy);
    }
    if (isPanning.current) {
      const dx = e.clientX - lastMouse.current.x;
      const dy = e.clientY - lastMouse.current.y;
      setPan(p => ({ x: p.x + dx, y: p.y + dy }));
      lastMouse.current = { x: e.clientX, y: e.clientY };
    }
  }, [zoom, moveNode]);

  const handleMouseUp = useCallback(() => {
    dragging.current = null;
    isPanning.current = false;
    if (canvasRef.current) canvasRef.current.style.cursor = 'default';
  }, []);

  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current || (e.target as HTMLElement).classList.contains('diagram-canvas__inner')) {
      if (connectingSource) {
        cancelConnect();
      } else {
        setSelectedId(null);
        onCanvasClick();
      }
    }
  }, [setSelectedId, onCanvasClick, connectingSource, cancelConnect]);

  // CU9: cuando el usuario clic sobre un nodo mientras está en modo conectar
  const handleNodeClick = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (activeTool === 'connect') {
      if (!connectingSource) {
        startConnect(id);
      } else {
        if (connectingSource === id) {
          cancelConnect();
        } else {
          // Mostrar picker de tipo de relación cerca del clic
          setPicker({ x: e.clientX, y: e.clientY, targetId: id });
        }
      }
    } else {
      setSelectedId(id);
    }
  }, [activeTool, connectingSource, startConnect, cancelConnect, setSelectedId]);

  const handlePickerSelect = useCallback((type: RelationType) => {
    if (picker) {
      finishConnect(picker.targetId, type);
      setPicker(null);
    }
  }, [picker, finishConnect]);

  const handleContextMenu = useCallback((e: React.MouseEvent, id?: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (id) setSelectedId(id);
    setCtxMenu({ x: e.clientX, y: e.clientY, targetId: id });
  }, [setSelectedId]);

  const getContextMenuOptions = (): ContextMenuOption[] => {
    if (ctxMenu?.targetId) {
      const node = nodes.find(n => n.id === ctxMenu.targetId);
      if (!node) return [];
      
      const isTable = (node as any).estereotipo === 'table';
      
      return [
        {
          label: 'Duplicar',
          icon: <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
          action: () => addNode(node.type, { ...node, id: undefined, x: node.x + 40, y: node.y + 40, nombre: `${node.nombre}_copy` } as any)
        },
        {
          label: isTable ? 'Convertir a Clase' : 'Convertir a Tabla',
          icon: <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16v16H4z"/><path d="M4 10h16M10 4v16"/></svg>,
          action: () => updateNode(node.id, { estereotipo: isTable ? undefined : 'table' } as any)
        },
        { separator: true, action: () => {} },
        {
          label: 'Eliminar',
          danger: true,
          icon: <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
          action: () => deleteNode(node.id)
        }
      ];
    } else {
      // Menu canvas vacio
      return [
        { label: 'Nueva Clase', action: () => addNode('class') },
        { label: 'Nueva Interfaz', action: () => addNode('interface') },
        { label: 'Nueva Tabla (BD)', action: () => {
           addNode('class');
           // the node will be created in context and we can't update it immediately by ID since it's generated there,
           // but we can add the feature inside addNode. For now, they can right click and 'Convertir a Tabla'.
        }},
        { separator: true, action: () => {} },
        { label: 'Nueva Nota', action: () => addNode('note') }
      ];
    }
  };

  // Calcular posiciones de nodos para RelationLayer (en canvas coords)
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

  return (
    <div
      className={`diagram-canvas${connectingSource ? ' diagram-canvas--connecting' : ''}`}
      ref={canvasRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onClick={handleCanvasClick}
      onContextMenu={(e) => handleContextMenu(e)}
    >
      {/* Grid background */}
      <div
        className="diagram-canvas__grid"
        style={{
          backgroundPosition: `${pan.x % (20 * zoom)}px ${pan.y % (20 * zoom)}px`,
          backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
        }}
      />

      {/* Content layer */}
      <div
        className="diagram-canvas__inner"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
        }}
      >
        {/* CU9: Capa SVG de relaciones */}
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
      </div>

      {/* Zoom badge */}
      <div className="diagram-canvas__zoom-badge">
        {Math.round(zoom * 100)}%
      </div>

      {/* CU9: Picker de tipo de relación */}
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
