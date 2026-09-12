from pydantic import BaseModel, EmailStr

class SolicitarRegistroOTPRequest(BaseModel):
    email: EmailStr

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    codigo_otp: str
