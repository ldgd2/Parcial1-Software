from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class DesarrolladorTareaInput(BaseModel):
    usuario_id: int
    nombre: str
    rol_ia: Optional[str] = None
    areas: Optional[List[str]] = None
    etiquetas: Optional[List[str]] = None


class RepartirTareasRequest(BaseModel):
    proyecto_id: int
    descripcion_proyecto: Optional[str] = None
    colaboradores: Optional[List[DesarrolladorTareaInput]] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    # False: solo calcula la propuesta (no crea tareas); se crean al aprobarla
    persistir: bool = True


class CrearTareaRequest(BaseModel):
    proyecto_id: int
    usuario_id: int
    tipo: Optional[str] = "desarrollo"
    area: Optional[str] = "general"
    titulo: str
    descripcion: Optional[str] = None
    orden: Optional[int] = 0
    estimacion_horas: Optional[int] = None   # CU37 (si falta, se calcula)
    complejidad: Optional[str] = None

