from pydantic import BaseModel

class UsuarioSimple(BaseModel):
    id: int
    nombre: str
    
    class Config:
        from_attributes = True

class SolicitudResponse(BaseModel):
    usuario_id: int
    estado: str
    rol_proyecto: str
    usuario: UsuarioSimple
    
    class Config:
        from_attributes = True
