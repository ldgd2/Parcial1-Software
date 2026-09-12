from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.registrar_usuario.schemas.request import UsuarioCreate, SolicitarRegistroOTPRequest
from backend.modules.gestion_usuarios.registrar_usuario.schemas.response import UsuarioResponse
from backend.modules.gestion_usuarios.registrar_usuario.services import user_service
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario

router = APIRouter(
    prefix="/usuarios",
    tags=["Gestion Usuarios"]
)

@router.post("/registro/solicitar-otp")
async def solicitar_registro_otp(data: SolicitarRegistroOTPRequest, db: AsyncSession = Depends(get_db)):
    return await user_service.solicitar_otp_registro(data.email, db)

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(user: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    return await user_service.registrar_nuevo_usuario(user, db)

@router.get("/me", response_model=UsuarioResponse)
async def obtener_usuario_actual(current_user: Usuario = Depends(get_current_user)):
    """Retorna el perfil del usuario autenticado actual."""
    return current_user

