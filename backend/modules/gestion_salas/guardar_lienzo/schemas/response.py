from pydantic import BaseModel


class GuardarLienzoResponse(BaseModel):
    detail: str
