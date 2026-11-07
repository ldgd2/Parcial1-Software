from typing import Optional
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
    effective_prompt = prompt or "Digitaliza este diagrama UML extrayendo todas sus clases, atributos, métodos y relaciones."
    return await generar_diagrama_desde_prompt(
        prompt=effective_prompt,
        image_base64=image_base64,
        provider=provider,
        api_key=api_key
    )
