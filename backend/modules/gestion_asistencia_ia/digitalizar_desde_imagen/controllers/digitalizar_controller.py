from fastapi import APIRouter, Depends
from ..schemas.digitalizar_schemas import DigitalizarRequest, DigitalizarResponse
from ..services.digitalizar_service import digitalizar_diagrama_desde_imagen
from backend.modules.gestion_usuarios.dependencies import get_current_user

router = APIRouter(prefix="/digitalizar", tags=["Asistencia IA - Digitalizar Imagen"])

@router.post("/imagen", response_model=DigitalizarResponse)
async def digitalizar_imagen(
    request: DigitalizarRequest,
    current_user: dict = Depends(get_current_user)
):
    resultado = await digitalizar_diagrama_desde_imagen(request.image_base64, request.prompt)
    return DigitalizarResponse(nodes=resultado.get("nodes", []), relations=resultado.get("relations", []))
