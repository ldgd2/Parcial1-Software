from pydantic import BaseModel
from typing import List, Optional


class ColaboradorRolOut(BaseModel):
    usuario_id: int
    nombre: str
    rol_ia: Optional[str] = None
    areas: List[str] = []
    responsabilidades: List[str] = []
    clases_asignadas: List[str] = []

    model_config = {"from_attributes": True}


class RepartirRolesResponse(BaseModel):
    proyecto_id: int
    resumen: str
    roles: List[ColaboradorRolOut]

