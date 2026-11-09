from pydantic import BaseModel
from typing import List, Optional


class TareaResponse(BaseModel):
    id: Optional[int] = None   # None en una propuesta todavía no aprobada
    proyecto_id: int
    usuario_id: int
    tipo: str
    area: Optional[str] = "general"
    titulo: str
    descripcion: Optional[str] = None
    completada: bool
    orden: int
    estimacion_horas: Optional[int] = None   # CU37
    complejidad: Optional[str] = None        # baja | media | alta

    model_config = {"from_attributes": True}


class RepartirTareasResponse(BaseModel):
    proyecto_id: int
    tareas_generadas: int
    tareas: List[TareaResponse]
    resumen: str

