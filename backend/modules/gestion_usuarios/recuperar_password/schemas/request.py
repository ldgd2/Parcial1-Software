from pydantic import BaseModel, EmailStr

class SolicitarOTPRequest(BaseModel):
    email: EmailStr

class VerificarOTPRequest(BaseModel):
    email: EmailStr
    codigo: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    codigo: str
    nueva_password: str
