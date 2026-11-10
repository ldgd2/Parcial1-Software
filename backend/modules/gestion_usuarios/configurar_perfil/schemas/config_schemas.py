from pydantic import BaseModel, Field
from typing import Optional

class ConfiguracionResponse(BaseModel):
    github_vinculado: bool
    github_username: Optional[str] = None
    db_configurada: bool
    email: Optional[str] = None
    nombre: Optional[str] = None

class ConfigurarDbRequest(BaseModel):
    codigo_otp: str
    db_password: str



class PerfilRequest(BaseModel):
    """CU05: datos personales editables."""
    nombre: str = Field(..., min_length=2, max_length=80)
