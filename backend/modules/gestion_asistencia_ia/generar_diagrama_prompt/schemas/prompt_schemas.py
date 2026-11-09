from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PromptRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    provider: Optional[str] = "gemini"
    api_key: Optional[str] = None
    proyecto_id: Optional[int] = None
    include_tasks: Optional[bool] = False
    image_base64: Optional[str] = None
    image_mime_type: Optional[str] = "image/png"
    # Diagrama ({nodes, relations}) antes de aplicar la respuesta: alimenta el historial de versiones
    estado_antes: Optional[Dict[str, Any]] = None
    autor: Optional[str] = None
    # Correcciones del diagrama ({id, target, text, estado}): la IA las recibe en la memoria
    correcciones: Optional[List[Dict[str, Any]]] = None

class PromptResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    summary: Optional[str] = None
    deletedNodes: Optional[List[Any]] = None
    deletedRelations: Optional[List[Any]] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    provider_used: Optional[str] = "gemini"
    # Versión del historial creada para esta interacción (el cliente envía luego el "después")
    version_id: Optional[int] = None
    # Tokens reales del pedido: {llamadas, entrada, salida, proveedores, estimado}
    uso_tokens: Optional[Dict[str, Any]] = None

class AudioRequest(BaseModel):
    audio_base64: str
    mime_type: str = "audio/webm"
    api_key: Optional[str] = None
