from fastapi import APIRouter, Depends
from ..schemas.digitalizar_schemas import DigitalizarRequest, DigitalizarResponse
from ..services.digitalizar_service import digitalizar_diagrama_desde_imagen
from backend.core import trabajos
from backend.modules.gestion_usuarios.dependencies import get_current_user

router = APIRouter(prefix="/digitalizar", tags=["Asistencia IA - Digitalizar Imagen"])


async def _digitalizar(request: DigitalizarRequest) -> DigitalizarResponse:
    resultado = await digitalizar_diagrama_desde_imagen(
        image_base64=request.image_base64,
        prompt=request.prompt,
        provider=request.provider,
        api_key=request.api_key
    )
    return DigitalizarResponse(
        nodes=resultado.get("nodes", []),
        relations=resultado.get("relations", []),
        provider_used=resultado.get("provider_used")
    )


@router.post("/imagen", response_model=DigitalizarResponse)
async def digitalizar_imagen(
    request: DigitalizarRequest,
    current_user=Depends(get_current_user)
):
    """Espera el resultado. Detrás de Cloudflare se corta a los 100 s: usar /imagen/iniciar."""
    return await _digitalizar(request)


@router.post("/imagen/iniciar")
async def iniciar_digitalizacion(request: DigitalizarRequest, current_user=Depends(get_current_user)):
    """Digitaliza en segundo plano (leer un diagrama grande puede tardar más de 100 s)."""
    return {"trabajo_id": trabajos.iniciar(current_user.id, lambda: _digitalizar(request)), "estado": "en_proceso"}


@router.get("/imagen/estado/{trabajo_id}")
async def estado_digitalizacion(trabajo_id: str, current_user=Depends(get_current_user)):
    return trabajos.estado(trabajo_id, current_user.id)
