from pydantic import BaseModel

class CompartirLinkResponse(BaseModel):
    codigo_acceso: str
    link: str


class MiembroResponse(BaseModel):
    usuario_id: int
    nombre: str
    email: str | None = None
    rol_proyecto: str
    estado: str
    permiso: str  # edit | view
    nivel: str    # anfitrion | editor | lector
