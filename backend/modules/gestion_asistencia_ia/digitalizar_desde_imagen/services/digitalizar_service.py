from typing import Optional
from backend.core.config import settings
from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services.prompt_service import generar_diagrama_desde_prompt

async def digitalizar_diagrama_desde_imagen(
    image_base64: str,
    prompt: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """
    Digitaliza un diagrama UML a partir de una imagen en base64 utilizando el gateway universal de IA.
    """
    # Kimi lee las fotos de diagramas mejor y es el proveedor principal del proyecto: si el servidor
    # lo tiene configurado va primero (los demás quedan de respaldo). Si el usuario puso SU llave
    # de otro proveedor, se respeta su elección.
    if settings.KIMI_API and not (api_key and (provider or "").lower() != "kimi"):
        provider = "kimi"
    effective_prompt = prompt or "Digitaliza este diagrama UML extrayendo todas sus clases, atributos, métodos y relaciones."
    return await generar_diagrama_desde_prompt(
        prompt=effective_prompt,
        image_base64=image_base64,
        provider=provider,
        api_key=api_key
    )
