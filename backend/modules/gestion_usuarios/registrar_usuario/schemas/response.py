from pydantic import BaseModel, EmailStr

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    tipo: str
    is_active: bool

    class Config:
        from_attributes = True
