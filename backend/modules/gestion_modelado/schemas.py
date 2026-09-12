from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Any, Dict
from datetime import datetime


# ─── CU8: Elementos ──────────────────────────────────────────────────────────

NodeType = Literal["class", "interface", "abstract", "enum", "note"]


class AtributoSchema(BaseModel):
    id: str
    visibilidad: Literal["+", "-", "#"]
    nombre: str
    tipo: str
    version: int = 0


class MetodoSchema(BaseModel):
    id: str
    visibilidad: Literal["+", "-", "#"]
    nombre: str
    parametros: str = ""
    retorno: str = "void"
    version: int = 0


class ElementContentSchema(BaseModel):
    atributos: List[AtributoSchema] = []
    metodos: List[MetodoSchema] = []
    valores: Optional[List[str]] = None      # Para enum
    contenido: Optional[str] = None          # Para nota


class CreateElementRequest(BaseModel):
    """CU8: Insertar un nuevo elemento en el diagrama."""
    id: str                    # ID generado en frontend
    proyecto_id: int
    type: NodeType
    nombre: str = "NuevaClase"
    color: Optional[str] = "#393E46"
    pos_x: int = 200
    pos_y: int = 200
    width: int = 220
    content: ElementContentSchema = Field(default_factory=ElementContentSchema)
    version: int = 0
    hash: str = ""


class UpdateElementRequest(BaseModel):
    """CU10: Editar un elemento existente."""
    nombre: Optional[str] = None
    color: Optional[str] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    width: Optional[int] = None
    content: Optional[ElementContentSchema] = None
    version: Optional[int] = None
    hash: Optional[str] = None


class ElementResponse(BaseModel):
    id: str
    proyecto_id: int
    type: NodeType
    nombre: str
    color: Optional[str]
    pos_x: Optional[int]
    pos_y: Optional[int]
    width: Optional[int]
    content: Dict[str, Any]
    version: int
    hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── CU9: Relaciones ─────────────────────────────────────────────────────────

RelationType = Literal[
    "association", "inheritance", "composition",
    "aggregation", "dependency", "realization", "directed"
]


class CreateRelationRequest(BaseModel):
    """CU9: Conectar dos elementos con una relación."""
    id: str
    proyecto_id: int
    type: RelationType
    source_id: str
    target_id: str
    label: str = ""
    source_label: str = ""
    target_label: str = ""
    version: int = 0
    hash: str = ""


class UpdateRelationRequest(BaseModel):
    """CU10 (relación): Editar una relación existente."""
    type: Optional[RelationType] = None
    label: Optional[str] = None
    source_label: Optional[str] = None
    target_label: Optional[str] = None
    version: Optional[int] = None
    hash: Optional[str] = None


class RelationResponse(BaseModel):
    id: str
    proyecto_id: int
    type: RelationType
    source_id: str
    target_id: str
    label: Optional[str]
    source_label: Optional[str]
    target_label: Optional[str]
    version: int
    hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
