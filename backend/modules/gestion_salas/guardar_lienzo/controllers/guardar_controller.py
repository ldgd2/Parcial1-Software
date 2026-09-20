from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_salas.guardar_lienzo.schemas.request import GuardarLienzoRequest
from backend.modules.gestion_salas.guardar_lienzo.schemas.response import GuardarLienzoResponse
from backend.modules.gestion_salas.guardar_lienzo.services.guardar_service import guardar_lienzo_service

router = APIRouter(prefix="/salas", tags=["Gestion Salas"])


@router.put("/{proyecto_id}/lienzo", response_model=GuardarLienzoResponse)
async def guardar_lienzo(
    proyecto_id: int,
    payload: GuardarLienzoRequest,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CU8 - Guardar Lienzo.
    Persiste el estado del diagrama. Solo colaboradores aprobados.
    """
    return await guardar_lienzo_service.guardar_lienzo(proyecto_id, payload, user, db)
