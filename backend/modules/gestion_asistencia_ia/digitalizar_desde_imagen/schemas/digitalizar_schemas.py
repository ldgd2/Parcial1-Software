from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DigitalizarRequest(BaseModel):
    image_base64: str
    prompt: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None

class DigitalizarResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    provider_used: Optional[str] = None
