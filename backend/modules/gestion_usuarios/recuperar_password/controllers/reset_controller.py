from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

from ..schemas.request import SolicitarOTPRequest, VerificarOTPRequest, ResetPasswordRequest
from ..services import reset_service

router = APIRouter(
    prefix="/usuarios/recuperar-password",
    tags=["Recuperar Password"]
)

@router.post("/solicitar")
async def solicitar_otp(data: SolicitarOTPRequest, db: AsyncSession = Depends(get_db)):
    """Genera y envía un OTP al correo si el usuario existe."""
    return await reset_service.generar_y_guardar_otp(data.email, db)

@router.post("/verificar")
async def verificar_otp(data: VerificarOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verifica si el OTP es válido y no ha expirado."""
    return await reset_service.verificar_otp(data.email, data.codigo, db)

@router.post("/reset")
async def restablecer_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Restablece la contraseña utilizando un OTP válido."""
    return await reset_service.restablecer_password(data.email, data.codigo, data.nueva_password, db)
