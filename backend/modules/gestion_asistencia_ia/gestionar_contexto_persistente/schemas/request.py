from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CorreccionInput(BaseModel):
    id: str = Field(..., description="ID único de la corrección")
    target: str = Field(..., description="Nombre del elemento o relación objetivo")
    text: str = Field(..., description="Texto breve de la corrección o requerimiento pendiente")
    estado: str = Field("abierta", description="Estado: abierta o resuelta")


class RegistrarInteraccionRequest(BaseModel):
    proyecto_id: int = Field(..., description="ID del proyecto asociado")
    user_prompt: str = Field(..., description="Instrucción enviada por el usuario")
    ai_summary: Optional[str] = Field(None, description="Resumen de la respuesta generada por la IA")
    intent: Optional[str] = Field("GENERAL", description="Intención detectada: REFACTOR, FIX, ROLES, TASKS, GENERAL")
    added_nodes: Optional[List[str]] = Field(default_factory=list, description="Lista de clases añadidas")
    updated_nodes: Optional[List[str]] = Field(default_factory=list, description="Lista de clases actualizadas")
    deleted_nodes: Optional[List[str]] = Field(default_factory=list, description="Lista de clases eliminadas")
    diagram_dsl: Optional[str] = Field(None, description="Instantánea actual del diagrama en Hyper-DSL")
    correcciones: Optional[List[CorreccionInput]] = Field(default_factory=list, description="Correcciones activas")
    estado_antes: Optional[Dict[str, Any]] = Field(None, description="DiagramState ({nodes, relations}) antes del cambio")
    estado_despues: Optional[Dict[str, Any]] = Field(None, description="DiagramState después del cambio (si ya se conoce)")
    autor: Optional[str] = Field(None, description="Nombre de quien pidió el cambio")
    propuesta: Optional[Dict[str, Any]] = Field(
        None, description="Cambios propuestos por la IA ({nodes, relations, deletedNodes, ...}); quedan pendientes de aprobación"
    )


class CrearVersionRequest(BaseModel):
    """Versión creada directamente (cambios manuales): no modifica la memoria de la IA."""
    intent: str = Field("MANUAL", max_length=40, description="MANUAL, IA, RESTAURAR…")
    cmd: str = Field("", max_length=2000, description="Descripción corta del cambio")
    resumen: str = Field("", max_length=2000)
    delta: str = Field("", max_length=500, description="+A,B | ~C | -D")
    autor: Optional[str] = Field(None, max_length=120)
    estado_antes: Optional[Dict[str, Any]] = None
    estado_despues: Optional[Dict[str, Any]] = None
    # Si se envía, la versión queda como propuesta pendiente de aprobación
    propuesta: Optional[Dict[str, Any]] = None


class DecidirPropuestaRequest(BaseModel):
    aceptar: bool = Field(..., description="True aprueba la propuesta, False la rechaza")
    estado_antes: Optional[Dict[str, Any]] = Field(
        None, description="Pizarra en el momento de aprobar (puede haber cambiado desde que la IA respondió)"
    )
    autor: Optional[str] = Field(None, max_length=120, description="Nombre de quien decide (si no hay sesión)")


class ActualizarVersionDespuesRequest(BaseModel):
    estado_despues: Dict[str, Any] = Field(..., description="DiagramState ({nodes, relations}) tras aplicar el cambio")


class GuardarSnapshotRequest(BaseModel):
    proyecto_id: int = Field(..., description="ID del proyecto")
    diagram_dsl: str = Field(..., description="Diagrama completo en formato Hyper-DSL")
    dominio: Optional[str] = Field(None, description="Dominio detectado del proyecto")
    resumen_acumulado: Optional[str] = Field(None, description="Resumen acumulado del estado arquitectónico")


class LimpiarMemoriaRequest(BaseModel):
    proyecto_id: int = Field(..., description="ID del proyecto a reiniciar")
    conservar_dominio: bool = Field(True, description="Si es True, conserva la categoría del dominio")


class CrearMemoriaRequest(BaseModel):
    """O bien `texto` (como en /recordar), o los campos explícitos."""
    texto: Optional[str] = Field(None, max_length=2000, description="'tema/sub: contenido' o texto libre")
    tipo: Optional[str] = Field(None, description="decision | restriccion | convencion | correccion | rechazo")
    topic_key: Optional[str] = Field(None, max_length=120)
    titulo: Optional[str] = Field(None, max_length=200)
    que: Optional[str] = Field(None, max_length=4000)
    por_que: Optional[str] = Field(None, max_length=2000)
    donde: Optional[str] = Field(None, max_length=500)
    aprendido: Optional[str] = Field(None, max_length=2000)
    autor: Optional[str] = Field(None, max_length=120)


class EditarMemoriaRequest(BaseModel):
    tipo: Optional[str] = None
    titulo: Optional[str] = Field(None, max_length=200)
    que: Optional[str] = Field(None, max_length=4000)
    por_que: Optional[str] = Field(None, max_length=2000)
    donde: Optional[str] = Field(None, max_length=500)
    aprendido: Optional[str] = Field(None, max_length=2000)


class ResolverConflictoRequest(BaseModel):
    mantener_nueva: bool = Field(..., description="True: queda la nueva; False: vuelve la anterior (la escrita a mano)")
