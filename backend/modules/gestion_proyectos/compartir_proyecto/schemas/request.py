from pydantic import BaseModel, EmailStr, Field


class InvitarRequest(BaseModel):
    email: EmailStr
    permiso: str = Field("edit", pattern="^(edit|view)$", description="edit = editor, view = lector")
