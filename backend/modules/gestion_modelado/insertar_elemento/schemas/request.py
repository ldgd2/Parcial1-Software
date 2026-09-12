from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

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
    valores: Optional[List[str]] = None    # Para enum
    contenido: Optional[str] = None        # Para nota


class InsertarElementoRequest(BaseModel):
    id: str
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
