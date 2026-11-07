from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DetectarErroresRequest(BaseModel):
    xml_content: Optional[str] = Field(None, description="Contenido XML/XMI exportado de Enterprise Architect u otra herramienta")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="Lista de nodos del lienzo actual si ya fueron parseados")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="Lista de relaciones del lienzo actual")
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto para consultar el lienzo en base de datos si no se envían nodos")


class CorregirErroresRequest(BaseModel):
    xml_content: Optional[str] = Field(None, description="Contenido XML a reparar")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="Nodos a reparar")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="Relaciones a reparar")
    errores_ids: Optional[List[str]] = Field(None, description="IDs específicos de errores a subsanar (si es None, subsana todos)")

