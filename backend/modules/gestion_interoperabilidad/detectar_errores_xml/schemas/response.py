from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorLogicoBD(BaseModel):
    id: str = Field(..., description="Identificador único del error")
    tipo: str = Field(..., description="Tipo de error (sin_pk, fk_huerfana, tipo_discordante, dependencia_circular, relacion_nm_directa, tabla_aislada, palabra_reservada)")
    severidad: str = Field(..., description="Severidad: alta, media, baja")
    tabla: str = Field(..., description="Nombre de la tabla/clase afectada")
    columna: Optional[str] = Field(None, description="Nombre del atributo o relación afectada")
    descripcion: str = Field(..., description="Explicación técnica del error lógico detectado")
    solucion_sugerida: str = Field(..., description="Solución recomendada o que aplicará el corrector")


class DetectarErroresResponse(BaseModel):
    total_errores: int
    es_valido: bool
    errores: List[ErrorLogicoBD]
    estadisticas: Dict[str, int]
    resumen: str


class CorregirErroresResponse(BaseModel):
    resumen: str
    errores_corregidos: int
    fixed_nodes: List[Dict[str, Any]]
    fixed_relations: List[Dict[str, Any]]
    fixed_xml: Optional[str] = None

