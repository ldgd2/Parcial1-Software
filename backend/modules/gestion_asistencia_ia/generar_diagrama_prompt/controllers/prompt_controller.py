from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.config import settings
from ..schemas.prompt_schemas import PromptRequest, PromptResponse, AudioRequest
from ..services.prompt_service import generar_diagrama_desde_prompt, transcribe_audio_with_gemini
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional

router = APIRouter(prefix="/prompt", tags=["Asistencia IA - Prompt"])

@router.get("/config")
async def get_prompt_config():
    """Retorna la configuración activa de proveedores de IA definida en .env."""
    return {
        "default_provider": settings.AI_PROVIDER,
        "has_gemini": bool(settings.GEMINI_API),
        "has_openrouter": bool(settings.OPENROUTE_API),
        "has_kimi": bool(settings.KIMI_API or settings.OPENROUTE_API),
        "models": {
            "gemini": "gemini-2.5-flash",
            "openrouter": settings.OPENROUTER_MODEL or settings.IA_MODEL,
            "kimi": settings.KIMI_MODEL,
            "kimi_vision": settings.KIMI_VISION_MODEL
        }
    }

@router.post("/generar", response_model=PromptResponse)
async def generar_diagrama(
    request: PromptRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    resultado = await generar_diagrama_desde_prompt(
        prompt=request.prompt,
        context=request.context,
        image_base64=request.image_base64,
        image_mime_type=request.image_mime_type or "image/png",
        provider=request.provider,
        api_key=request.api_key,
        proyecto_id=request.proyecto_id,
        db=db
    )
    return PromptResponse(
        nodes=resultado.get("nodes", []),
        relations=resultado.get("relations", []),
        summary=resultado.get("summary", ""),
        deletedNodes=resultado.get("deletedNodes"),
        deletedRelations=resultado.get("deletedRelations"),
        tasks=resultado.get("tasks"),
        provider_used=resultado.get("provider_used", settings.AI_PROVIDER)
    )

@router.post("/transcribe-audio")
async def transcribe_audio(
    request: AudioRequest,
    current_user = Depends(get_current_user_optional)
):
    transcripcion = await transcribe_audio_with_gemini(
        request.audio_base64,
        request.mime_type,
        request.api_key
    )
    return {"text": transcripcion}
