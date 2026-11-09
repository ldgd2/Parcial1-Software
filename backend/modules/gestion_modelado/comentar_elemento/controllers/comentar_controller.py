from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from ..schemas.request import CrearComentarioRequest, ActualizarComentarioRequest
from ..schemas.response import ComentarioResponse
from ..services.comentar_service import ComentarService

router = APIRouter(prefix="/api/modelado/comentarios", tags=["Modelado - Comentar Elemento"])


@router.post("", response_model=ComentarioResponse)
async def crear_comentario(
    req: CrearComentarioRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
) -> ComentarioResponse:
    service = ComentarService(db)
    autor_id = current_user.id if current_user else None
    autor_nombre = getattr(current_user, "nombre", None) if current_user else (req.autor_nombre or "Colaborador")
    if req.autor_ia:
        # Lo escribe la IA; se conserva autor_id de quien aprobó para saber quién fue
        autor_nombre = f"IA (aprobado por {autor_nombre})" if current_user or req.autor_nombre else "IA"
    return await service.agregar_comentario(req, autor_id=autor_id, autor_nombre=autor_nombre)


@router.get("/elemento/{elemento_id}", response_model=List[ComentarioResponse])
async def obtener_comentarios_elemento(
    elemento_id: str,
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional)
) -> List[ComentarioResponse]:
    service = ComentarService(db)
    return await service.listar_comentarios_elemento(proyecto_id, elemento_id)


@router.get("/proyecto/{proyecto_id}", response_model=List[ComentarioResponse])
async def obtener_todos_comentarios_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional)
) -> List[ComentarioResponse]:
    service = ComentarService(db)
    return await service.listar_todos_comentarios_proyecto(proyecto_id)


@router.patch("/{comentario_id}", response_model=ComentarioResponse)
async def actualizar_comentario(
    comentario_id: str,
    req: ActualizarComentarioRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional)
) -> ComentarioResponse:
    service = ComentarService(db)
    return await service.actualizar_comentario(comentario_id, req)


@router.delete("/{comentario_id}")
async def eliminar_comentario(
    comentario_id: str,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional)
) -> dict:
    service = ComentarService(db)
    return await service.eliminar_comentario(comentario_id)

