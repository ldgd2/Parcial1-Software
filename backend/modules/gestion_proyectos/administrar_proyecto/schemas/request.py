from pydantic import BaseModel
from typing import Optional

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class ResolverSolicitud(BaseModel):
    aprobar: bool
