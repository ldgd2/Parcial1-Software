from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ColaboradorRolInput(BaseModel):
    usuario_id: int
    nombre: str
    etiquetas: Optional[List[str]] = None


class RepartirRolesRequest(BaseModel):
    proyecto_id: int
    colaboradores: Optional[List[ColaboradorRolInput]] = None
    instrucciones: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None


class AsignarRolManualRequest(BaseModel):
    proyecto_id: int
    usuario_id: int
    rol_ia: str
    areas: List[str]
    responsabilidades: Optional[List[str]] = None

