from pydantic import BaseModel, EmailStr, Field


class InvitarRequest(BaseModel):
    email: EmailStr
    permiso: str = Field("editor", description="editor | lector")


class PermisoRequest(BaseModel):
    permiso: str = Field(..., description="editor | lector")
