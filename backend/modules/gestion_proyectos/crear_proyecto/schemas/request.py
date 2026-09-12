from pydantic import BaseModel
from typing import Optional

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
