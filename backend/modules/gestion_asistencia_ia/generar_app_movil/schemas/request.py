from pydantic import BaseModel
from typing import Optional, Dict, Any


class GenerarAppMovilRequest(BaseModel):
    proyecto_id: int
    diagram_json: Optional[Dict[str, Any]] = None
    api_base_url: Optional[str] = "http://localhost:8080"
    app_name: Optional[str] = "app_movil"
    use_ia_refinement: Optional[bool] = False


class RefinarVistaRequest(BaseModel):
    proyecto_id: int
    vista_nombre: str
    codigo_actual: str
    instrucciones: str
    api_endpoint: Optional[str] = None

