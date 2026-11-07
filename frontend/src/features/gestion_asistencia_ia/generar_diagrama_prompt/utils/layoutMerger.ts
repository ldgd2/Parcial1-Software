import type { ClassNode } from '@/features/gestion_modelado/shared/types/types';

interface RawAiNode {
  id: string;
  name?: string;
  nombre?: string;
  type?: string;
  attributes?: string[];
  atributos?: string[];
  methods?: string[];
  metodos?: string[];
  x?: number;
  y?: number;
}

const ACADEMIC_TIERS: Record<string, { row: number; priority: number }> = {
  usuario: { row: 0, priority: 1 },
  docente: { row: 0, priority: 2 },
  estudiante: { row: 0, priority: 3 },
  administrador: { row: 0, priority: 4 },
  persona: { row: 0, priority: 5 },

  facultad: { row: 1, priority: 1 },
  carrera: { row: 1, priority: 2 },
  materia: { row: 1, priority: 3 },
  curso: { row: 1, priority: 4 },
  aula: { row: 1, priority: 5 },
  departamento: { row: 1, priority: 6 },

  inscripcion: { row: 2, priority: 1 },
  tarea: { row: 2, priority: 2 },
  entrega: { row: 2, priority: 3 },
  calificacion: { row: 2, priority: 4 },

  revision: { row: 3, priority: 1 },
  comentario: { row: 3, priority: 2 },
  notificacion: { row: 3, priority: 3 },
};

/**
 * Calcula posiciones libres de colisión en el lienzo para que ejecuciones paralelas de IA
 * no superpongan clases en las mismas coordenadas.
 * Si isRefactoring es true, organiza las clases en capas semánticas arquitectónicas unificadas.
 */
export function calculateSafeNodePositions(
  rawAiNodes: RawAiNode[],
  existingNodes: ClassNode[],
  parallelOffsetIndex: number = 0,
  isRefactoring: boolean = false
): { id: string; name: string; type: string; attributes: string[]; methods: string[]; x: number; y: number }[] {
  if (!rawAiNodes || rawAiNodes.length === 0) return [];

  // Modo refactorización: Organización arquitectónica por capas semánticas (elimina islas desconectadas)
  if (isRefactoring) {
    const rowCounts: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
    const sortedNodes = [...rawAiNodes].sort((a, b) => {
      const aName = (a.name || a.nombre || '').toLowerCase().trim();
      const bName = (b.name || b.nombre || '').toLowerCase().trim();
      const aTier = ACADEMIC_TIERS[aName] || { row: 4, priority: 99 };
      const bTier = ACADEMIC_TIERS[bName] || { row: 4, priority: 99 };
      if (aTier.row !== bTier.row) return aTier.row - bTier.row;
      return aTier.priority - bTier.priority;
    });

    return sortedNodes.map((node, index) => {
      const nodeName = node.name || node.nombre || 'Clase';
      const nameLower = nodeName.toLowerCase().trim();
      const tier = ACADEMIC_TIERS[nameLower] || { row: 4, priority: 99 };
      const row = tier.row;
      const col = rowCounts[row] || 0;
      rowCounts[row] = col + 1;

      const matched = existingNodes.find(
        en => en.id === node.id || (Boolean(en.nombre) && Boolean(nodeName) && en.nombre.toLowerCase().trim() === nameLower)
      );

      return {
        id: matched ? matched.id : (node.id || `node_${Date.now()}_${index}`),
        name: nodeName,
        type: node.type || (matched ? matched.type : 'class'),
        attributes: node.attributes || node.atributos || [],
        methods: node.methods || node.metodos || [],
        x: 100 + (col * 280),
        y: 100 + (row * 280)
      };
    });
  }

  // Calcular límites actuales del diagrama existente para evitar islas horizontales desconectadas
  let minX = 100;
  let minY = 100;
  let maxX = 100;
  let maxY = 100;

  if (existingNodes.length > 0) {
    minX = Math.min(...existingNodes.map(n => n.x || 100));
    minY = Math.min(...existingNodes.map(n => n.y || 100));
    maxX = Math.max(...existingNodes.map(n => (n.x || 0) + (n.width || 220)));
    maxY = Math.max(...existingNodes.map(n => (n.y || 0) + 240));
  }

  const shouldPlaceBelow = existingNodes.length > 0 && ((maxX - minX) > 420 || existingNodes.length >= 3);

  const staggerX = (parallelOffsetIndex % 4) * 60;
  const staggerY = Math.floor(parallelOffsetIndex / 4) * 80;

  const originX = existingNodes.length === 0
    ? 120 + staggerX
    : (shouldPlaceBelow ? minX + staggerX : Math.min(maxX + 40, 900) + staggerX);

  const originY = existingNodes.length === 0
    ? 120 + staggerY
    : (shouldPlaceBelow ? maxY + 50 + staggerY : minY + staggerY);

  return rawAiNodes.map((node, index) => {
    const nodeName = node.name || node.nombre || 'Clase';
    const nameLower = nodeName.toLowerCase().trim();
    
    // Si la clase ya existe con el mismo nombre o ID, reutilizar sus coordenadas
    const matched = existingNodes.find(
      en => en.id === node.id || (Boolean(en.nombre) && Boolean(nodeName) && en.nombre.toLowerCase().trim() === nameLower)
    );

    if (matched) {
      return {
        id: matched.id,
        name: nodeName,
        type: node.type || matched.type || 'class',
        attributes: node.attributes || node.atributos || [],
        methods: node.methods || node.metodos || [],
        x: matched.x,
        y: matched.y
      };
    }

    // Nueva clase: distribuir en cuadrícula compacta (3 columnas)
    const col = index % 3;
    const row = Math.floor(index / 3);

    return {
      id: node.id || `node_${Date.now()}_${index}`,
      name: nodeName,
      type: node.type || 'class',
      attributes: node.attributes || node.atributos || [],
      methods: node.methods || node.metodos || [],
      x: Math.round(originX + (col * 270)),
      y: Math.round(originY + (row * 240))
    };
  });
}
