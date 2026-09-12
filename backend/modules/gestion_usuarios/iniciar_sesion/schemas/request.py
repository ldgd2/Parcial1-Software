from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AnonimoCreate(BaseModel):
    nombre: str
