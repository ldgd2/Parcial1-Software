// ─── Atributos y Métodos ─────────────────────────────────────────────────────

export interface Atributo {
  id: string;
  visibilidad: '+' | '-' | '#' | 'PK' | 'FK';
  nombre: string;
  tipo: string;
  version: number;
}

export interface Metodo {
  id: string;
  visibilidad: '+' | '-' | '#';
  nombre: string;
  parametros: string;
  retorno: string;
  version: number;
}

// ─── CU8: Tipos de elementos del diagrama ────────────────────────────────────

export type NodeType = 'class' | 'interface' | 'enum' | 'abstract' | 'note';

export interface ClassNode {
  id: string;
  type: NodeType;
  x: number;
  y: number;
  width?: number;
  nombre: string;
  color: string;
  atributos: Atributo[];
  metodos: Metodo[];
  version: number;
  hash: string;
  
  // Opcionales según el tipo (CU8)
  valores?: string[]; // Para enum
  contenido?: string; // Para nota
  estereotipo?: string; // Para UML standard o tablas DB (ej. 'table')

  // VCS Local (Offline)
  offlineVersion?: number;
  isOfflineDirty?: boolean;
}

// ─── CU9: Relaciones / Conexiones ────────────────────────────────────────────

export type RelationType =
  | 'association'    // Asociación → línea simple con flecha
  | 'inheritance'    // Herencia   → línea con triángulo vacío
  | 'composition'    // Composición → línea con rombo relleno
  | 'aggregation'    // Agregación  → línea con rombo vacío
  | 'dependency'     // Dependencia → línea punteada con flecha
  | 'realization'    // Realización → línea punteada con triángulo vacío
  | 'directed'       // Asociación dirigida → flecha simple
  | '1:1'            // Base de Datos: 1 a 1
  | '1:N'            // Base de Datos: 1 a Muchos
  | 'N:M'            // Base de Datos: Muchos a Muchos
  | '0..1:1'         // Base de Datos: 0..1 a 1
  | '0..1:N'         // Base de Datos: 0..1 a Muchos
  | '0..N:1'         // Base de Datos: 0..N a 1
  | '0..N:M';        // Base de Datos: 0..N a Muchos

export interface Relation {
  id: string;
  type: RelationType;
  sourceId: string;   // ID del nodo origen
  targetId: string;   // ID del nodo destino
  label?: string;     // Etiqueta opcional en la relación
  sourceLabel?: string; // Multiplicidad origen (ej. "1")
  targetLabel?: string; // Multiplicidad destino (ej. "*")
  version: number;
  hash: string;
}

export interface Correccion {
  id: string;
  targetId: string;
  texto: string;
  autorId: number;
  autorNombre: string;
  fecha: number;
  estado: 'abierta' | 'resuelta';
  fechaResolucion?: number;
  resueltoPorId?: number;
  resueltoPorNombre?: string;
}

// ─── Estado completo del diagrama ────────────────────────────────────────────

export interface DiagramState {
  nodes: ClassNode[];
  relations: Relation[];  // CU9: relaciones persistidas
  correcciones?: Record<string, Correccion[]>;
  version: number;
}

export interface SalaInfo {
  proyecto_id: number;
  proyecto_nombre: string;
  codigo_acceso: string;
  lienzo_json: string | null;
}

