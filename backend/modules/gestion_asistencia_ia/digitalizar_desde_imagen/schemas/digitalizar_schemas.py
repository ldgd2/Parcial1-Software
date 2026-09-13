from pydantic import BaseModel
from typing import List, Dict, Any

class DigitalizarRequest(BaseModel):
    image_base64: str

class DigitalizarResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
