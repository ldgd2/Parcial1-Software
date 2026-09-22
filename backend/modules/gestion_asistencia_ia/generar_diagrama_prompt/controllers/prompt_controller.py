from fastapi import APIRouter, Depends
from ..schemas.prompt_schemas import PromptRequest, PromptResponse, AudioRequest
from ..services.prompt_service import generar_diagrama_desde_prompt, transcribe_audio_with_gemini
from backend.modules.gestion_usuarios.dependencies import get_current_user

router = APIRouter(prefix="/prompt", tags=["Asistencia IA - Prompt"])

@router.post("/generar", response_model=PromptResponse)
async def generar_diagrama(
    request: PromptRequest,
    current_user: dict = Depends(get_current_user)
):
    resultado = await generar_diagrama_desde_prompt(request.prompt, request.context)
    return PromptResponse(
        nodes=resultado.get("nodes", []),
        relations=resultado.get("relations", []),
        summary=resultado.get("summary", "")
    )

@router.post("/transcribe-audio")
async def transcribe_audio(
    request: AudioRequest,
    current_user: dict = Depends(get_current_user)
):
    transcripcion = await transcribe_audio_with_gemini(request.audio_base64, request.mime_type)
    return {"text": transcripcion}
