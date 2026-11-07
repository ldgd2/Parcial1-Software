from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from backend.modules.gestion_asistencia_ia.repartir_roles.schemas.request import (
    RepartirRolesRequest,
    AsignarRolManualRequest,
)
from backend.modules.gestion_asistencia_ia.repartir_roles.schemas.response import (
    ColaboradorRolOut,
    RepartirRolesResponse,
)
from backend.modules.gestion_asistencia_ia.repartir_roles.services.roles_service import (
    ejecutar_reparticion_roles,
    asignar_rol_manualmente,
    listar_roles_proyecto,
)

router = APIRouter(prefix="/api/ia/roles", tags=["IA - Repartición de Roles"])


@router.post("/repartir", response_model=RepartirRolesResponse)
async def repartir_roles(
    req: RepartirRolesRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> RepartirRolesResponse:
    return await ejecutar_reparticion_roles(req, db)


@router.get("/proyecto/{proyecto_id}", response_model=List[ColaboradorRolOut])
async def obtener_roles_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> List[ColaboradorRolOut]:
    return await listar_roles_proyecto(proyecto_id, db)


@router.put("/asignar", response_model=ColaboradorRolOut)
async def asignar_rol_manual(
    req: AsignarRolManualRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> ColaboradorRolOut:
    return await asignar_rol_manualmente(req, db)

