from typing import Optional
from pydantic import BaseModel, Field


class CrearComentarioRequest(BaseModel):
    proyecto_id: int = Field(..., description="ID del proyecto")
    elemento_id: str = Field(..., description="ID del nodo o relación a comentar")
    elemento_tipo: str = Field("node", description="Tipo de elemento: node o relation")
    texto: str = Field(..., min_length=1, description="Contenido del comentario o nota técnica")
    autor_nombre: Optional[str] = Field("Colaborador", description="Nombre del usuario o autor")


class ActualizarComentarioRequest(BaseModel):
    texto: Optional[str] = Field(None, min_length=1, description="Texto modificado del comentario")
    estado: Optional[str] = Field(None, description="Estado: abierto o resuelto")

