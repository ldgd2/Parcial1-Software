from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

NodeType = Literal["class", "interface", "abstract", "enum", "note"]
RelationType = Literal[
    "association", "inheritance", "composition",
    "aggregation", "dependency", "realization", "directed"
]


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
    valores: Optional[List[str]] = None
    contenido: Optional[str] = None


class EditarElementoRequest(BaseModel):
    """Solo los campos que se desean cambiar. Posición no sube versión."""
    nombre: Optional[str] = None
    color: Optional[str] = None
    pos_x: Optional[int] = None          # No semántico
    pos_y: Optional[int] = None          # No semántico
    width: Optional[int] = None          # No semántico
    content: Optional[ElementContentSchema] = None
    version: Optional[int] = None
    hash: Optional[str] = None


class EditarRelacionRequest(BaseModel):
    type: Optional[RelationType] = None
    label: Optional[str] = None
    source_label: Optional[str] = None
    target_label: Optional[str] = None
    version: Optional[int] = None
    hash: Optional[str] = None


class ElementoResponse(BaseModel):
    id: str
    proyecto_id: int
    type: NodeType
    nombre: str
    color: Optional[str]
    pos_x: Optional[int]
    pos_y: Optional[int]
    width: Optional[int]
    content: dict
    version: int
    hash: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RelacionResponse(BaseModel):
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

    model_config = {"from_attributes": True}
