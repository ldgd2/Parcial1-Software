from pydantic import BaseModel
from typing import Optional, Dict


class ArchivoGenerado(BaseModel):
    ruta: str
    contenido: str


class AppMovilResponse(BaseModel):
    proyecto_id: int
    app_name: str
    archivos_generados: int
    resumen: str
    archivos: Dict[str, str]


class RefinarVistaResponse(BaseModel):
    codigo_refinado: str
    resumen_cambios: str

