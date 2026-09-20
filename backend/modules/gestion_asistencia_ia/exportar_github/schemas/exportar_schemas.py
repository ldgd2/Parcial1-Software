from pydantic import BaseModel
from typing import Dict, Any, Optional

class GithubAuthCallback(BaseModel):
    code: str

class ExportarProyectoRequest(BaseModel):
    proyecto_id: int
    nombre_repo: str
    diagram_json: Dict[str, Any]
    auto_deploy: Optional[bool] = False

class ExportarProyectoResponse(BaseModel):
    url_repositorio: str
    mensaje: str
    api_docs_md: str | None = None
