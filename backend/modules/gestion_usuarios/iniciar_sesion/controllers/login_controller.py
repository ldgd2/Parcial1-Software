from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.iniciar_sesion.schemas.request import LoginRequest, AnonimoCreate
from backend.modules.gestion_usuarios.iniciar_sesion.schemas.response import TokenResponse
from backend.modules.gestion_usuarios.iniciar_sesion.services import login_service

router = APIRouter(
    prefix="/usuarios",
    tags=["Gestion Usuarios"]
)

@router.post("/login", response_model=TokenResponse)
async def iniciar_sesion(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Inicia sesión para un usuario registrado."""
    return await login_service.autenticar_usuario(login_data, db)

@router.post("/ingreso-anonimo", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def ingreso_anonimo(data: AnonimoCreate, db: AsyncSession = Depends(get_db)):
    """Permite el ingreso público a un usuario que entra solo con su nombre. Devuelve un JWT limitado."""
    return await login_service.registrar_ingreso_anonimo(data, db)
