import React, { useRef, useState, useCallback, useEffect, useMemo } from 'react';
import { Hand, MousePointer2, Minus, Plus, Maximize } from 'lucide-react';
import { useDiagram } from '@/features/gestion_modelado/shared/context/DiagramContext';
import { ClassNode as ClassNodeComponent } from '@/features/gestion_modelado/editar_elemento/components/ClassNode/ClassNode';
import { RelationLayer } from '@/features/gestion_modelado/conectar_elemento/components/RelationLayer/RelationLayer';
import { ConnectPicker } from '@/features/gestion_modelado/conectar_elemento/components/ConnectPicker/ConnectPicker';
import { ContextMenu, type ContextMenuOption } from '@/features/gestion_modelado/lienzo_principal/components/ContextMenu/ContextMenu';
import { CommentThreadModal, type ComentarioElemento } from '@/features/gestion_modelado/comentar_elemento';
import {
  listarTodosComentariosProyecto,
  crearComentarioElemento,
  actualizarComentarioElemento,
  eliminarComentarioElemento
} from '@/features/gestion_modelado/comentar_elemento/services/comentarService';
import type { RelationType } from '@/features/gestion_modelado/shared/types/types';
import './DiagramCanvas.css';

const MIN_ZOOM = 0.2;
const MAX_ZOOM = 3;
const clampZoom = (z: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));
/** Margen (en unidades del diagrama) alrededor del contenido para las barras y "ajustar". */
const CONTENT_PAD = 200;
const FIT_PAD_PX = 80;
const SCROLLBAR_SIZE = 8;
const SCROLLBAR_INSET = 4;

const isTypingTarget = (t: EventTarget | null) => {
  const el = t as HTMLElement | null;
  if (!el) return false;
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) || el.isContentEditable;
};

interface Props {
  onCanvasClick: () => void;
  proyectoId?: number;
}

export const DiagramCanvas: React.FC<Props> = ({ onCanvasClick, proyectoId }) => {
  const { nodes, addNode, updateNode, deleteNode, deleteRelation, moveNode, selectedIds, setSelectedIds, connectingSource, activeTool, setActiveTool, startConnect, finishConnect, cancelConnect } = useDiagram();
  const canvasRef = useRef<HTMLDivElement>(null);

  // Pan & zoom en un solo estado para que el zoom hacia el cursor sea consistente
  const [view, setView] = useState({ x: 0, y: 0, zoom: 1 });
  const pan = useMemo(() => ({ x: view.x, y: view.y }), [view.x, view.y]);
  const zoom = view.zoom;
  const setPan = useCallback(
    (fn: (p: { x: number; y: number }) => { x: number; y: number }) =>
      setView(v => ({ ...v, ...fn({ x: v.x, y: v.y }) })),
    []
  );
  const isPanning = useRef(false);
  const lastMouse = useRef({ x: 0, y: 0 });

  // Herramienta mano (estilo Figma): H la activa, V vuelve a selección,
  // mantener Espacio la activa temporalmente. El botón central también panea.
  const [handTool, setHandTool] = useState(false);
  const [spaceHeld, setSpaceHeld] = useState(false);
  const [isGrabbing, setIsGrabbing] = useState(false);
  const handActive = handTool || spaceHeld;

  // Tamaño visible del lienzo (barras de desplazamiento y "ajustar al contenido")
  const [viewport, setViewport] = useState({ w: 0, h: 0 });
  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setViewport({ w: entry.contentRect.width, h: entry.contentRect.height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  /** Zoom manteniendo fijo el punto (cx, cy) de la pantalla; por defecto el centro. */
  const zoomAt = useCallback((factor: number | ((current: number) => number), cx?: number, cy?: number) => {
    setView(v => {
      const z = clampZoom(typeof factor === 'function' ? factor(v.zoom) : v.zoom * factor);
      const px = cx ?? viewport.w / 2;
      const py = cy ?? viewport.h / 2;
      const worldX = (px - v.x) / v.zoom;
      const worldY = (py - v.y) / v.zoom;
      return { x: px - worldX * z, y: py - worldY * z, zoom: z };
    });
  }, [viewport.w, viewport.h]);

  // Multi-Drag
  const dragging = useRef<{ items: { id: string; startX: number; startY: number; nodeX: number; nodeY: number }[] } | null>(null);

  // Marquee Selection
  const [marquee, setMarquee] = useState<{ startX: number, startY: number, endX: number, endY: number } | null>(null);

  // CU9: picker de tipo de relación
  const [picker, setPicker] = useState<{ x: number; y: number; targetId: string } | null>(null);

  // Context Menu
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; targetId?: string } | null>(null);

  // Comentarios colaborativos en elementos del diagrama
  const [activeCommentElement, setActiveCommentElement] = useState<{ id: string; name: string; type: 'node' | 'relation' } | null>(null);
  const [allComments, setAllComments] = useState<ComentarioElemento[]>([]);

  const refreshComments = useCallback(async () => {
    if (proyectoId && proyectoId > 0) {
      try {
        const list = await listarTodosComentariosProyecto(proyectoId);
        setAllComments(list);
      } catch (err) {
        console.warn('[DiagramCanvas] Error cargando comentarios:', err);
      }
    }
  }, [proyectoId]);

  useEffect(() => {
    refreshComments();
  }, [refreshComments]);

  // Comentarios que deja la IA al aplicarse una propuesta (aquí o en otro cliente de la sala)
  useEffect(() => {
    let t: ReturnType<typeof setTimeout> | null = null;
    const pronto = () => { if (t) clearTimeout(t); t = setTimeout(refreshComments, 600); };
    const alMensaje = (e: Event) => {
      const m = (e as CustomEvent<any>).detail;
      if (m?.propuesta?.estado === 'aprobada') pronto();
    };
    window.addEventListener('comentarios_actualizados', pronto);
    window.addEventListener('remote_chat_message', alMensaje);
    return () => {
      window.removeEventListener('comentarios_actualizados', pronto);
      window.removeEventListener('remote_chat_message', alMensaje);
      if (t) clearTimeout(t);
    };
  }, [refreshComments]);

  const commentCountsByElement = useMemo(() => {
    const map: Record<string, number> = {};
    for (const c of allComments) {
      if (c.estado === 'abierto') {
        map[c.elemento_id] = (map[c.elemento_id] || 0) + 1;
      }
    }
    return map;
  }, [allComments]);

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
      nombre: n.nombre,
      x: n.x,
      y: n.y,
      width: n.width || 220,
      height,
    };
  });

  // Límites del contenido en coordenadas del diagrama
  const bounds = nodePositions.length
    ? {
        minX: Math.min(...nodePositions.map(n => n.x)),
        minY: Math.min(...nodePositions.map(n => n.y)),
        maxX: Math.max(...nodePositions.map(n => n.x + n.width)),
        maxY: Math.max(...nodePositions.map(n => n.y + n.height)),
      }
    : null;

  const fitToContent = () => {
    if (!bounds || !viewport.w || !viewport.h) {
      setView({ x: 0, y: 0, zoom: 1 });
      return;
    }
    const bw = Math.max(1, bounds.maxX - bounds.minX);
    const bh = Math.max(1, bounds.maxY - bounds.minY);
    const z = clampZoom(Math.min(
      (viewport.w - FIT_PAD_PX * 2) / bw,
      (viewport.h - FIT_PAD_PX * 2) / bh,
      1
    ));
    setView({
      x: (viewport.w - bw * z) / 2 - bounds.minX * z,
      y: (viewport.h - bh * z) / 2 - bounds.minY * z,
      zoom: z,
    });
  };
  const fitRef = useRef(fitToContent);
  const zoomAtRef = useRef(zoomAt);
  useEffect(() => {
    fitRef.current = fitToContent;
    zoomAtRef.current = zoomAt;
  });

  // Atajos de navegación: H (mano), V (selección), Espacio mantenido, Shift+1 (ajustar), Shift+0 (100%)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target)) return;
      if (e.code === 'Space') {
        e.preventDefault(); // evita scroll de la página y "clic" en el botón enfocado
        if (!e.repeat) setSpaceHeld(true);
        return;
      }
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.shiftKey && e.code === 'Digit1') { e.preventDefault(); fitRef.current(); return; }
      if (e.shiftKey && e.code === 'Digit0') {
        e.preventDefault();
        zoomAtRef.current(() => 1);
        return;
      }
      if (!e.shiftKey && e.key.toLowerCase() === 'h') setHandTool(true);
      if (!e.shiftKey && e.key.toLowerCase() === 'v') setHandTool(false);
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') setSpaceHeld(false);
    };
    const onBlur = () => setSpaceHeld(false);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur', onBlur);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur', onBlur);
    };
  }, []);

  /** true si el evento ocurre sobre la superficie del diagrama (no en menús, modales o controles). */
  const isCanvasSurface = (target: EventTarget | null) => {
    const el = target as HTMLElement | null;
    if (!el || !canvasRef.current) return false;
    return el === canvasRef.current || !!el.closest('.diagram-canvas__inner');
  };

  // Fase de captura: con la mano activa (o botón central) se panea aunque se pulse sobre un nodo
  const handleMouseDownCapture = useCallback((e: React.MouseEvent) => {
    if (!isCanvasSurface(e.target)) return;
    if (e.button === 1 || (e.button === 0 && handActive)) {
      e.preventDefault();
      e.stopPropagation();
      isPanning.current = true;
      setIsGrabbing(true);
      lastMouse.current = { x: e.clientX, y: e.clientY };
    }
  }, [handActive]);

  // Con la mano activa, los clics no seleccionan ni editan elementos
  const handleClickCapture = useCallback((e: React.MouseEvent) => {
    if (handActive && isCanvasSurface(e.target)) e.stopPropagation();
  }, [handActive]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
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
      // Rueda sola = zoom hacia la posición del cursor
      const rect = canvasRef.current?.getBoundingClientRect();
      const factor = e.deltaY > 0 ? 0.9 : 1.1;
      if (rect) {
        zoomAtRef.current(factor, e.clientX - rect.left, e.clientY - rect.top);
      } else {
        zoomAtRef.current(factor);
      }
    }
  }, [setPan]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('wheel', handleWheel, { passive: false });
    }
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIds.length > 0) {
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;
        selectedIds.forEach(id => {
          deleteNode(id);
          deleteRelation(id);
        });
        setSelectedIds([]);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);

    return () => { 
      if (canvas) canvas.removeEventListener('wheel', handleWheel); 
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleWheel, selectedIds, deleteNode, deleteRelation, setSelectedIds]);

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
  }, [zoom, moveNode, pan, marquee, nodePositions, setSelectedIds, setPan]);

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
    setIsGrabbing(false);
    setMarquee(null);
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

  // ── Barras de desplazamiento ──────────────────────────────────────────
  // El rango desplazable es la unión del contenido (con margen) y lo que se ve ahora.
  const visX = -view.x / zoom;
  const visY = -view.y / zoom;
  const visW = viewport.w / zoom;
  const visH = viewport.h / zoom;
  const rangeMinX = Math.min(visX, (bounds?.minX ?? visX) - CONTENT_PAD);
  const rangeMaxX = Math.max(visX + visW, (bounds?.maxX ?? visX + visW) + CONTENT_PAD);
  const rangeMinY = Math.min(visY, (bounds?.minY ?? visY) - CONTENT_PAD);
  const rangeMaxY = Math.max(visY + visH, (bounds?.maxY ?? visY + visH) + CONTENT_PAD);
  const showHBar = !!bounds && viewport.w > 0 && rangeMaxX - rangeMinX > visW + 1;
  const showVBar = !!bounds && viewport.h > 0 && rangeMaxY - rangeMinY > visH + 1;

  const buildBar = (axis: 'x' | 'y') => {
    const isX = axis === 'x';
    const track = (isX ? viewport.w : viewport.h) - SCROLLBAR_INSET * 2
      - ((isX ? showVBar : showHBar) ? SCROLLBAR_SIZE + SCROLLBAR_INSET : 0);
    const rangeMin = isX ? rangeMinX : rangeMinY;
    const range = (isX ? rangeMaxX : rangeMaxY) - rangeMin;
    const vis = isX ? visW : visH;
    const visStart = isX ? visX : visY;
    const thumb = Math.max(32, track * (vis / range));
    const free = Math.max(1, track - thumb);
    const scrollable = Math.max(1, range - vis);
    const offset = ((visStart - rangeMin) / scrollable) * free;
    // Píxeles de pan por cada píxel que se mueve el pulgar
    const panPerPx = (scrollable / free) * zoom;
    return { track, thumb, offset, panPerPx, rangeMin, scrollable, free };
  };
  const hBar = showHBar ? buildBar('x') : null;
  const vBar = showVBar ? buildBar('y') : null;

  const startScrollDrag = (axis: 'x' | 'y', startClient: number, startPanValue: number, panPerPx: number) => {
    const onMove = (ev: MouseEvent) => {
      const d = (axis === 'x' ? ev.clientX : ev.clientY) - startClient;
      const next = startPanValue - d * panPerPx;
      setView(v => (axis === 'x' ? { ...v, x: next } : { ...v, y: next }));
    };
    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  const handleThumbMouseDown = (axis: 'x' | 'y', e: React.MouseEvent) => {
    const bar = axis === 'x' ? hBar : vBar;
    if (!bar || e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    startScrollDrag(axis, axis === 'x' ? e.clientX : e.clientY, axis === 'x' ? view.x : view.y, bar.panPerPx);
  };

  // Clic en la pista: centra el pulgar en ese punto y permite seguir arrastrando
  const handleTrackMouseDown = (axis: 'x' | 'y', e: React.MouseEvent) => {
    const bar = axis === 'x' ? hBar : vBar;
    if (!bar || e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const pos = axis === 'x' ? e.clientX - rect.left : e.clientY - rect.top;
    const thumbStart = Math.min(bar.free, Math.max(0, pos - bar.thumb / 2));
    const worldStart = bar.rangeMin + (thumbStart / bar.free) * bar.scrollable;
    const nextPan = -worldStart * zoom;
    setView(v => (axis === 'x' ? { ...v, x: nextPan } : { ...v, y: nextPan }));
    startScrollDrag(axis, axis === 'x' ? e.clientX : e.clientY, nextPan, bar.panPerPx);
  };

  const canvasClass = [
    'diagram-canvas',
    connectingSource ? 'diagram-canvas--connecting' : '',
    handActive ? 'diagram-canvas--hand' : '',
    isGrabbing ? 'diagram-canvas--grabbing' : '',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={canvasClass}
      ref={canvasRef}
      onMouseDownCapture={handleMouseDownCapture}
      onClickCapture={handleClickCapture}
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
        <RelationLayer
          nodePositions={nodePositions}
          commentCounts={commentCountsByElement}
          onOpenComments={(id, name) => setActiveCommentElement({ id, name, type: 'relation' })}
        />

        {nodes.map(node => (
          <div key={node.id} onContextMenu={(e) => handleContextMenu(e, node.id)}>
            <ClassNodeComponent
              node={node}
              onDragStart={(e) => startNodeDrag(node.id, e, node.x, node.y)}
              onNodeClick={(e) => handleNodeClick(node.id, e)}
              isConnectingMode={!!connectingSource}
              isConnectingSource={connectingSource === node.id}
              commentCount={commentCountsByElement[node.id] || 0}
              onOpenComments={(id, name, type) => setActiveCommentElement({ id, name, type })}
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

      {hBar && (
        <div
          className="diagram-canvas__scrollbar diagram-canvas__scrollbar--h"
          style={{ width: hBar.track }}
          onMouseDown={(e) => handleTrackMouseDown('x', e)}
        >
          <div
            className="diagram-canvas__scroll-thumb"
            style={{ width: hBar.thumb, transform: `translateX(${hBar.offset}px)` }}
            onMouseDown={(e) => handleThumbMouseDown('x', e)}
          />
        </div>
      )}
      {vBar && (
        <div
          className="diagram-canvas__scrollbar diagram-canvas__scrollbar--v"
          style={{ height: vBar.track }}
          onMouseDown={(e) => handleTrackMouseDown('y', e)}
        >
          <div
            className="diagram-canvas__scroll-thumb"
            style={{ height: vBar.thumb, transform: `translateY(${vBar.offset}px)` }}
            onMouseDown={(e) => handleThumbMouseDown('y', e)}
          />
        </div>
      )}

      {/* Controles de navegación */}
      <div className="diagram-canvas__hud" onMouseDown={(e) => e.stopPropagation()}>
        <button
          type="button"
          className={`diagram-canvas__hud-btn${!handActive ? ' is-active' : ''}`}
          onClick={() => setHandTool(false)}
          title="Seleccionar (V)"
          aria-label="Herramienta de selección"
          aria-pressed={!handActive}
        >
          <MousePointer2 size={15} />
        </button>
        <button
          type="button"
          className={`diagram-canvas__hud-btn${handActive ? ' is-active' : ''}`}
          onClick={() => setHandTool(h => !h)}
          title="Mano para mover el lienzo (H) · o mantén Espacio"
          aria-label="Herramienta mano"
          aria-pressed={handActive}
        >
          <Hand size={15} />
        </button>
        <span className="diagram-canvas__hud-sep" aria-hidden="true" />
        <button type="button" className="diagram-canvas__hud-btn" onClick={() => zoomAt(1 / 1.2)} title="Alejar" aria-label="Alejar">
          <Minus size={15} />
        </button>
        <button
          type="button"
          className="diagram-canvas__hud-btn diagram-canvas__hud-zoom"
          onClick={() => zoomAt(() => 1)}
          title="Restablecer al 100% (Shift+0)"
          aria-label={`Zoom ${Math.round(zoom * 100)}%, restablecer al 100%`}
        >
          {Math.round(zoom * 100)}%
        </button>
        <button type="button" className="diagram-canvas__hud-btn" onClick={() => zoomAt(1.2)} title="Acercar" aria-label="Acercar">
          <Plus size={15} />
        </button>
        <button type="button" className="diagram-canvas__hud-btn" onClick={fitToContent} title="Ajustar al contenido (Shift+1)" aria-label="Ajustar al contenido">
          <Maximize size={15} />
        </button>
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

      {activeCommentElement && (
        <CommentThreadModal
          isOpen={!!activeCommentElement}
          onClose={() => setActiveCommentElement(null)}
          elementoId={activeCommentElement.id}
          elementName={activeCommentElement.name}
          elementoTipo={activeCommentElement.type}
          comentarios={allComments.filter(c => c.elemento_id === activeCommentElement.id)}
          onAgregar={async (texto) => {
            if (!proyectoId) return;
            const nuevo = await crearComentarioElemento({
              proyecto_id: proyectoId,
              elemento_id: activeCommentElement.id,
              elemento_tipo: activeCommentElement.type,
              texto,
              autor_nombre: 'Colaborador'
            });
            await refreshComments();
            return nuevo;
          }}
          onCambiarEstado={async (id, nuevoEstado) => {
            const updated = await actualizarComentarioElemento(id, { estado: nuevoEstado });
            await refreshComments();
            return updated;
          }}
          onEliminar={async (id) => {
            const res = await eliminarComentarioElemento(id);
            await refreshComments();
            return res;
          }}
        />
      )}
    </div>
  );
};
