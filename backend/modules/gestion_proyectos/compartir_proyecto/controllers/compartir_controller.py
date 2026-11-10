from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_proyectos.compartir_proyecto.schemas.response import CompartirLinkResponse
from backend.modules.gestion_proyectos.compartir_proyecto.services import compartir_service, invitar_service
from backend.modules.gestion_proyectos.compartir_proyecto.schemas.request import InvitarRequest
from backend.modules.gestion_proyectos.compartir_proyecto.schemas.response import MiembroResponse
from backend.modules.gestion_proyectos.crear_proyecto.schemas.response import ProyectoResponse

router = APIRouter(
    prefix="/proyectos",
    tags=["Gestion Proyectos"]
)

@router.get("/compartidos-conmigo", response_model=List[ProyectoResponse])
async def compartidos_conmigo(user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """CU08: proyectos de otros anfitriones en los que el usuario es colaborador aprobado."""
    return await invitar_service.compartidos_conmigo(db, user)


@router.post("/{proyecto_id}/invitar", response_model=MiembroResponse, status_code=status.HTTP_201_CREATED)
async def invitar(
    proyecto_id: int,
    req: InvitarRequest,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU08: el anfitrión comparte el proyecto con un usuario registrado, con permiso 'edit' o 'view'.
    Ver y cambiar el permiso de los miembros: /api/proyectos/{id}/miembros (permisos_proyecto)."""
    return await invitar_service.invitar_por_correo(db, proyecto_id, req.email, req.permiso, user)


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
