from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ColaboradorResponse(BaseModel):
    usuario_id: int
    rol_proyecto: str
    estado: str

    class Config:
        from_attributes = True

class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    codigo_acceso: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    colaboradores: Optional[List[ColaboradorResponse]] = []

    class Config:
        from_attributes = True
