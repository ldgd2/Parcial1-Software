from fastapi import APIRouter, Depends
from ..schemas.prompt_schemas import PromptRequest, PromptResponse
from ..services.prompt_service import generar_diagrama_desde_prompt
from backend.modules.gestion_usuarios.dependencies import get_current_user

router = APIRouter(prefix="/prompt", tags=["Asistencia IA - Prompt"])

@router.post("/generar", response_model=PromptResponse)
async def generar_diagrama(
    request: PromptRequest,
    current_user: dict = Depends(get_current_user)
):
    resultado = await generar_diagrama_desde_prompt(request.prompt)
    return PromptResponse(nodes=resultado.get("nodes", []), relations=resultado.get("relations", []))
