from pydantic import BaseModel

class CompartirLinkResponse(BaseModel):
    codigo_acceso: str
    link: str
