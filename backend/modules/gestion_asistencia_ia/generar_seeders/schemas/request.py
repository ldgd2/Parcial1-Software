from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GenerarSeedersRequest(BaseModel):
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto para obtener el diagrama desde BD si no se envía")
    diagram_json: Optional[Dict[str, Any]] = Field(None, description="Estructura {nodes, relations} del diagrama actual")
    cantidad_por_tabla: int = Field(10, ge=1, le=100, description="Cantidad de registros de prueba coherentes a generar por cada tabla")
    formato: str = Field("sql", description="Formato de salida: 'sql', 'java_runner', 'json'")

