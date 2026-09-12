from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_proyectos.crear_proyecto.schemas.response import ProyectoResponse
from backend.modules.gestion_proyectos.administrar_proyecto.schemas.request import ProyectoUpdate, ResolverSolicitud
from backend.modules.gestion_proyectos.administrar_proyecto.schemas.response import SolicitudResponse
from backend.modules.gestion_proyectos.administrar_proyecto.services import admin_service

router = APIRouter(
    prefix="/proyectos",
    tags=["Gestion Proyectos"]
)

@router.put("/{proyecto_id}", response_model=ProyectoResponse)
async def actualizar_proyecto(
    proyecto_id: int,
    data: ProyectoUpdate,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza el nombre o descripción del proyecto. Solo el anfitrión."""
    return await admin_service.actualizar_proyecto(proyecto_id, data, user, db)

@router.delete("/{proyecto_id}")
async def eliminar_proyecto(
    proyecto_id: int,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Elimina el proyecto permanentemente. Solo el anfitrión."""
    return await admin_service.eliminar_proyecto(proyecto_id, user, db)

@router.get("/{proyecto_id}/solicitudes", response_model=List[SolicitudResponse])
async def ver_solicitudes(
    proyecto_id: int,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ve todos los usuarios que han solicitado unirse al proyecto vía código UUID y están pendientes."""
    return await admin_service.obtener_solicitudes(proyecto_id, user, db)

@router.post("/{proyecto_id}/solicitudes/{solicitante_id}")
async def resolver_solicitud(
    proyecto_id: int,
    solicitante_id: int,
    data: ResolverSolicitud,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """El anfitrión aprueba o rechaza una solicitud pendiente."""
    return await admin_service.resolver_solicitud(proyecto_id, solicitante_id, data, user, db)
