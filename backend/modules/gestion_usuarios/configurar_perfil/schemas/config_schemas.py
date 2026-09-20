from pydantic import BaseModel
from typing import Optional

class ConfiguracionResponse(BaseModel):
    github_vinculado: bool
    github_username: Optional[str] = None
    db_configurada: bool

class ConfigurarDbRequest(BaseModel):
    db_password: str
