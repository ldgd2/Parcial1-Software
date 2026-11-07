from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GenerarSeedersResponse(BaseModel):
    resumen: str
    total_tablas: int
    total_registros: int
    orden_insercion: List[str] = Field(..., description="Orden topológico respetando las restricciones de integridad referencial")
    registros_por_tabla: Dict[str, int]
    sql_script: str = Field(..., description="Script SQL ejecutable en PostgreSQL con INSERTs coherentes")
    java_code: Optional[str] = Field(None, description="Código CommandLineRunner para Spring Boot si se solicita")

