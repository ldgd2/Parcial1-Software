from fastapi import APIRouter, Depends
from backend.modules.gestion_usuarios.cerrar_sesion.schemas.response import MessageResponse
from backend.modules.gestion_usuarios.cerrar_sesion.services import logout_service
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario

router = APIRouter(
    prefix="/usuarios",
    tags=["Gestion Usuarios"]
)

@router.post("/logout", response_model=MessageResponse)
async def cerrar_sesion(current_user: Usuario = Depends(get_current_user)):
    return logout_service.procesar_cierre_sesion()
