from pydantic import BaseModel
from typing import Optional


class LienzoResponse(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    codigo_acceso: str
    lienzo_json: str
    rol_proyecto: str
    # CU38: nivel del usuario en el proyecto: lector | editor | anfitrion
    permiso: Optional[str] = None
    github_repo_url: Optional[str] = None
