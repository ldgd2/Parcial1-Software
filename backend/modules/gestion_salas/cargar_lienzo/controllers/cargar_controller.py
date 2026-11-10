from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_salas.cargar_lienzo.schemas.response import LienzoResponse
from backend.modules.gestion_salas.cargar_lienzo.services.cargar_service import cargar_lienzo_service

router = APIRouter(prefix="/salas", tags=["Gestion Salas"])


@router.get("/{proyecto_id}/lienzo", response_model=LienzoResponse)
async def cargar_lienzo(
    proyecto_id: int,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CU8 - Cargar Lienzo.
    Retorna el estado actual del diagrama del proyecto.
    Solo colaboradores aprobados pueden acceder.
    """
    nivel = await verificar_permiso(db, user, proyecto_id, "lector")   # CU43: antes cargaba cualquier proyecto
    respuesta = await cargar_lienzo_service.cargar_lienzo(proyecto_id, user, db)
    respuesta.permiso = nivel   # CU38: lector | editor | anfitrion (el frontend ajusta la sala)
    return respuesta
