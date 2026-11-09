from pydantic import BaseModel
from typing import List, Optional


class HabilidadDesarrollador(BaseModel):
    usuario_id: int
    nombre: str
    etiquetas: List[str]


class GenerarEquipoRequest(BaseModel):
    proyecto_id: int
    descripcion_proyecto: str
    desarrolladores: List[HabilidadDesarrollador]
    # False: la IA solo propone (no se guarda nada); las tareas se crean al aprobar
    persistir: bool = True


class TareaIAOut(BaseModel):
    id: Optional[int] = None   # None en una propuesta todavía no aprobada
    proyecto_id: int
    usuario_id: int
    tipo: str
    titulo: str
    descripcion: Optional[str]
    completada: bool
    orden: int
    estimacion_horas: Optional[int] = None   # CU37
    complejidad: Optional[str] = None

    model_config = {"from_attributes": True}


class ActualizarHabilidadesRequest(BaseModel):
    etiquetas: List[str]
