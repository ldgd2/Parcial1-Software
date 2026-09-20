from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_salas.unirse_sala.schemas.response import UnirseSalaResponse
from backend.modules.gestion_salas.unirse_sala.services.unirse_service import unirse_sala_service

router = APIRouter(prefix="/salas", tags=["Gestion Salas"])


@router.get("/unirse/{codigo_acceso}", response_model=UnirseSalaResponse)
async def unirse_sala(
    codigo_acceso: str,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CU7 - Unirse a Sala.
    Verifica el código de acceso, crea la solicitud si es nuevo colaborador,
    y retorna los datos del proyecto para cargar la sala.
    """
    return await unirse_sala_service.unirse_a_sala(codigo_acceso, user, db)
