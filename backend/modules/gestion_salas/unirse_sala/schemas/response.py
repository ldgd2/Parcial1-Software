from pydantic import BaseModel
from typing import Optional


class UnirseSalaResponse(BaseModel):
    acceso: str
    mensaje: Optional[str] = None
    proyecto_id: int
    proyecto_nombre: str
    codigo_acceso: Optional[str] = None
    lienzo_json: Optional[str] = None
    github_repo_url: Optional[str] = None
