from typing import Optional
from pydantic import BaseModel


class ComentarioResponse(BaseModel):
    id: str
    proyecto_id: int
    elemento_id: str
    elemento_tipo: str
    autor_id: Optional[int] = None
    autor_nombre: str
    texto: str
    estado: str
    created_at: str
    updated_at: str

