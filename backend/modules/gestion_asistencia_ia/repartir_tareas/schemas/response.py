from pydantic import BaseModel
from typing import List, Optional


class TareaResponse(BaseModel):
    id: int
    proyecto_id: int
    usuario_id: int
    tipo: str
    area: Optional[str] = "general"
    titulo: str
    descripcion: Optional[str] = None
    completada: bool
    orden: int

    model_config = {"from_attributes": True}


class RepartirTareasResponse(BaseModel):
    proyecto_id: int
    tareas_generadas: int
    tareas: List[TareaResponse]
    resumen: str

