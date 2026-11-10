from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from backend.modules.gestion_proyectos_asistida.repartir_roles.schemas.request import (
    RepartirRolesRequest,
    AsignarRolManualRequest,
)
from backend.modules.gestion_proyectos_asistida.repartir_roles.schemas.response import (
    ColaboradorRolOut,
    RepartirRolesResponse,
)
from backend.modules.gestion_proyectos_asistida.repartir_roles.services.roles_service import (
    ejecutar_reparticion_roles,
    asignar_rol_manualmente,
    listar_roles_proyecto,
)


router = APIRouter(prefix="/api/ia/roles", tags=["Gestión de Proyectos Asistida - Repartición de Roles"])


@router.post("/repartir", response_model=RepartirRolesResponse)
async def repartir_roles(
    req: RepartirRolesRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> RepartirRolesResponse:
    await verificar_permiso(db, usuario, req.proyecto_id, "editor")
    return await ejecutar_reparticion_roles(req, db)


@router.get("/proyecto/{proyecto_id}", response_model=List[ColaboradorRolOut])
async def obtener_roles_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> List[ColaboradorRolOut]:
    return await listar_roles_proyecto(proyecto_id, db)


@router.put("/asignar", response_model=ColaboradorRolOut)
async def asignar_rol_manual(
    req: AsignarRolManualRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> ColaboradorRolOut:
    # También lo usa la aprobación de roles propuestos por la IA → editor
    await verificar_permiso(db, usuario, req.proyecto_id, "editor")
    return await asignar_rol_manualmente(req, db)
