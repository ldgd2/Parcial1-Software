from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_proyectos.crear_proyecto.schemas.request import ProyectoCreate
from backend.modules.gestion_proyectos.crear_proyecto.schemas.response import ProyectoResponse
from backend.modules.gestion_proyectos.crear_proyecto.services import crear_service
from backend.modules.gestion_proyectos.administrar_proyecto.services import admin_service

router = APIRouter(
    prefix="/proyectos",
    tags=["Gestion Proyectos"]
)

@router.get("/mis-proyectos", response_model=List[ProyectoResponse])
async def listar_mis_proyectos(
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista todos los proyectos donde el usuario autenticado es colaborador aprobado."""
    return await admin_service.listar_mis_proyectos(user, db)

@router.post("/", response_model=ProyectoResponse, status_code=status.HTTP_201_CREATED)
async def crear_proyecto(
    data: ProyectoCreate, 
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crea un nuevo proyecto y asigna al creador como anfitrión aprobado."""
    return await crear_service.crear_nuevo_proyecto(data, user, db)

