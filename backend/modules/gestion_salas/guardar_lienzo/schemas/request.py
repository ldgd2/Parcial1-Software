from pydantic import BaseModel
from typing import Any


class GuardarLienzoRequest(BaseModel):
    lienzo: Any
