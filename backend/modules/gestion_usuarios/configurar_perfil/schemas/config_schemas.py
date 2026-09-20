from pydantic import BaseModel
from typing import Optional

class ConfiguracionResponse(BaseModel):
    github_vinculado: bool
    github_username: Optional[str] = None
    db_configurada: bool
    email: Optional[str] = None

class ConfigurarDbRequest(BaseModel):
    codigo_otp: str
    db_password: str

