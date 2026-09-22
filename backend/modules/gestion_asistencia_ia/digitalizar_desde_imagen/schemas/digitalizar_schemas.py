from pydantic import BaseModel
from typing import List, Dict, Any

class DigitalizarRequest(BaseModel):
    image_base64: str
    prompt: str | None = None

class DigitalizarResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
