from typing import List, Optional
from pydantic import BaseModel, Field


class EventoEpisodico(BaseModel):
    ts: int = Field(..., description="Timestamp Unix de la interacción")
    intent: str = Field(..., description="Intención: REFACTOR, FIX, ROLES, TASKS, ADD, DEL")
    cmd: str = Field(..., description="Instrucción condensada")
    delta: str = Field(..., description="Diferencias aplicadas (+Nodos, -Nodos)")
    summary: str = Field(..., description="Resumen breve de la acción aplicada")


class CorreccionItem(BaseModel):
    id: str = Field(..., description="ID de la corrección")
    target: str = Field(..., description="Elemento o relación objetivo")
    text: str = Field(..., description="Observación o pendiente")
    estado: str = Field(..., description="abierta o resuelta")


class ContextoIAResponse(BaseModel):
    id: int
    proyecto_id: int
    dominio: str
    resumen_acumulado: str
    historial_comprimido: List[EventoEpisodico]
    correcciones: List[CorreccionItem]
    snapshot_dsl: str
    tokens_ahorrados_estimados: int
    version: int
    contexto_compilado_llm: str
    fecha_actualizacion: Optional[str] = None


class CompilarContextoResponse(BaseModel):
    proyecto_id: int
    contexto_compilado_llm: str
    tokens_estimados: int
    tokens_ahorrados: int
    total_eventos_recordados: int
    correcciones_activas_count: int

