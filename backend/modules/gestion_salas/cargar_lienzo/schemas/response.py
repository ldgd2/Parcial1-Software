from pydantic import BaseModel
from typing import Optional


class LienzoResponse(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    codigo_acceso: str
    lienzo_json: str
    rol_proyecto: str
    github_repo_url: Optional[str] = None
