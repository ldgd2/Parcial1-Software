from pydantic import BaseModel
from typing import List, Optional


class HabilidadDesarrollador(BaseModel):
    usuario_id: int
    nombre: str
    etiquetas: List[str]


class GenerarEquipoRequest(BaseModel):
    proyecto_id: int
    descripcion_proyecto: str
    desarrolladores: List[HabilidadDesarrollador]


class TareaIAOut(BaseModel):
    id: int
    proyecto_id: int
    usuario_id: int
    tipo: str
    titulo: str
    descripcion: Optional[str]
    completada: bool
    orden: int

    model_config = {"from_attributes": True}


class ActualizarHabilidadesRequest(BaseModel):
    etiquetas: List[str]
