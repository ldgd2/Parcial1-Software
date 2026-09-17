from pydantic import BaseModel
from typing import Dict, Any, Optional

class GithubAuthCallback(BaseModel):
    code: str

class ExportarProyectoRequest(BaseModel):
    nombre_repo: str
    diagram_json: Dict[str, Any]

class ExportarProyectoResponse(BaseModel):
    url_repositorio: str
    mensaje: str
