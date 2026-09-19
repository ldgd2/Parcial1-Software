from pydantic import BaseModel
from typing import List, Dict, Any

class PromptRequest(BaseModel):
    prompt: str
    context: str | None = None

class PromptResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
