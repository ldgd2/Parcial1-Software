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


class GuardarSnapshotRequest(BaseModel):
    proyecto_id: int = Field(..., description="ID del proyecto")
    diagram_dsl: str = Field(..., description="Diagrama completo en formato Hyper-DSL")
    dominio: Optional[str] = Field(None, description="Dominio detectado del proyecto")
    resumen_acumulado: Optional[str] = Field(None, description="Resumen acumulado del estado arquitectónico")


class LimpiarMemoriaRequest(BaseModel):
    proyecto_id: int = Field(..., description="ID del proyecto a reiniciar")
    conservar_dominio: bool = Field(True, description="Si es True, conserva la categoría del dominio")

