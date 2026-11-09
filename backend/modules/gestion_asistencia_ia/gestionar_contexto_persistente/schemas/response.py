from typing import Any, Dict, List, Optional
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


class AccionMemoria(BaseModel):
    ts: int = 0
    intent: str
    cmd: str
    summary: str
    delta: str


class CorreccionMemoria(BaseModel):
    target: str
    text: str


class MemoriaPrompt(BaseModel):
    tipo: str
    topic_key: str
    titulo: str
    que: str
    aprendido: str


class MemoriaSecciones(BaseModel):
    """La memoria inyectada en el prompt, por partes (misma selección que el texto)."""
    dominio: str
    resumen: str
    ultimas_acciones: List[AccionMemoria]
    correcciones_abiertas: List[CorreccionMemoria]
    total_correcciones_abiertas: int
    diagrama_dsl: str
    memorias: List[MemoriaPrompt] = []


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
    memoria_secciones: Optional[MemoriaSecciones] = None
    # Versión creada por esta operación (solo en registrar_interaccion)
    version_id: Optional[int] = None


class CompilarContextoResponse(BaseModel):
    proyecto_id: int
    contexto_compilado_llm: str
    tokens_estimados: int
    tokens_ahorrados: int
    total_eventos_recordados: int
    correcciones_activas_count: int
    memoria_secciones: Optional[MemoriaSecciones] = None


class VersionResumen(BaseModel):
    id: int
    ts: int
    intent: str
    cmd: str
    resumen: str
    delta: str
    autor: Optional[str] = None
    tiene_antes: bool
    tiene_despues: bool
    # Propuestas de la IA: None (no es propuesta) | pendiente | aprobada | rechazada
    estado_propuesta: Optional[str] = None
    decidida_por: Optional[str] = None
    decidida_en: Optional[int] = None   # Unix


class VersionDetalle(VersionResumen):
    estado_antes: Optional[Dict[str, Any]] = None
    estado_despues: Optional[Dict[str, Any]] = None
    propuesta: Optional[Dict[str, Any]] = None


class VersionesPagina(BaseModel):
    items: List[VersionResumen]
    hay_mas: bool


class MemoriaItem(BaseModel):
    """Observación de la memoria del proyecto (estilo Engram)."""
    id: int
    tipo: str
    topic_key: str
    titulo: str
    que: str
    por_que: str
    donde: str
    aprendido: str
    origen: str
    autor: Optional[str] = None
    vigente: bool
    en_conflicto: bool
    reemplaza_id: Optional[int] = None
    version_id: Optional[int] = None
    creada: int
    actualizada: int
