from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_proyectos.compartir_proyecto.schemas.response import CompartirLinkResponse
from backend.modules.gestion_proyectos.compartir_proyecto.services import compartir_service

router = APIRouter(
    prefix="/proyectos",
    tags=["Gestion Proyectos"]
)

@router.get("/{proyecto_id}/link-compartir", response_model=CompartirLinkResponse)
async def obtener_link_compartir(
    proyecto_id: int,
    request: Request,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Devuelve el link público para invitar a otros usuarios. Solo anfitriones."""
    return await compartir_service.obtener_link_compartir(proyecto_id, request, user, db)

@router.post("/unirse/{codigo_acceso}")
async def solicitar_unirse(
    codigo_acceso: str,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Un usuario registrado o anónimo utiliza un código de acceso para solicitar entrar a un proyecto."""
    return await compartir_service.solicitar_unirse(codigo_acceso, user, db)
