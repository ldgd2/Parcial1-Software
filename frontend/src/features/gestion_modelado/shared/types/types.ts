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

export type NodeType =
  | 'class'
  | 'interface'
  | 'abstract'
  | 'enum'
  | 'datatype'
  | 'primitive'
  | 'signal'
  | 'note'
  | 'part'
  | 'port'
  | 'expose_interface'
  | 'auxillary'
  | 'focus'
  | 'implementation_class'
  | 'realization_class'
  | 'specification'
  | 'type'
  | 'utility'
  | 'create_event'
  | 'destroy_event'
  | 'constraint'
  | 'text'
  | 'artifact'
  | 'requirement'
  | 'issue'
  | 'change'
  | 'information_item'
  | 'boundary';

export interface ClassNode {
  id: string;
  type: NodeType;
  x: number;
  y: number;
  width?: number;
  height?: number;
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

// ────────────────────────────────────────────────────────────────────────────
// 🟪 CU9: Relaciones / Conexiones 
// ────────────────────────────────────────────────────────────────────────────

export type RelationType =
  | 'association'    // Asociación — línea simple con flecha
  | 'inheritance'    // Herencia   — línea con triángulo vacío
  | 'composition'    // Composición — línea con rombo relleno
  | 'aggregation'    // Agregación  — línea con rombo vacío
  | 'dependency'     // Dependencia — línea punteada con flecha
  | 'realization'    // Realización — línea punteada con triángulo vacío
  | 'directed'       // Asociación dirigida — flecha simple
  | 'association_class' // Clase Asociación
  | 'template_binding'  // Enlace de plantilla
  | 'instantiate'       // Instancia (Instantiates)
  | 'instantiated_by'   // Instantiated by
  | 'substitution'      // Sustitución
  | 'usage'             // Uso
  | 'trace'             // Trazabilidad
  | 'information_flow'  // Flujo de información
  | 'abstraction'       // Abstracción
  | 'calls'             // Llamadas (Calls)
  | 'called_by'         // Llamadas (Called by)
  | 'create'            // Create
  | 'send'              // Send
  | 'aggregation_to_whole'
  | 'aggregation_to_part'
  | 'composition_to_whole'
  | 'composition_to_part'
  | 'assembly'          // Assembly
  | 'connector'         // Connector
  | 'delegate'          // Delegate
  | '1:1'            // Base de Datos: 1 a 1
  | '1:N'            // Base de Datos: 1 a Muchos
  | 'N:M'            // Base de Datos: Muchos a Muchos
  | '0..1:1'         // Base de Datos: 0..1 a 1
  | '0..1:N'         // Base de Datos: 0..1 a Muchos
  | '0..N:1'         // Base de Datos: 0..N a 1
  | '0..N:M';        // Base de Datos: 0..N a Muchos

export type EndpointSide = 'top' | 'bottom' | 'left' | 'right';

/** Ancla de extremo de relación: posición relativa al nodo (sobrevive cuando el nodo se mueve) */
export interface RelationEndpoint {
  side: EndpointSide;
  t: number; // 0..1 a lo largo del lado
}

export interface Relation {
  id: string;
  type: RelationType;
  sourceId: string;
  targetId: string;
  label?: string;
  sourceLabel?: string;
  targetLabel?: string;
  version: number;
  hash: string;
  waypoints?: { x: number; y: number }[];
  sourceEndpoint?: RelationEndpoint; // ancla del extremo origen (fijada por el usuario)
  targetEndpoint?: RelationEndpoint; // ancla del extremo destino (fijada por el usuario)
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
  github_repo_url?: string | null;
}

