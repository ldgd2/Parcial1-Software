from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from fastapi import HTTPException
from sqlalchemy import select
from backend.modules.gestion_modelado.models import ComentarioElemento
from ..schemas.request import CrearComentarioRequest, ActualizarComentarioRequest
from ..schemas.response import ComentarioResponse
from ..services.comentar_service import ComentarService

router = APIRouter(prefix="/api/modelado/comentarios", tags=["Modelado - Comentar Elemento"])


@router.post("", response_model=ComentarioResponse)
async def crear_comentario(
    req: CrearComentarioRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(usuario_requerido())
) -> ComentarioResponse:
    await verificar_permiso(db, current_user, req.proyecto_id, "lector")   # un lector también puede comentar
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
    _ = Depends(requiere_proyecto("lector"))
) -> List[ComentarioResponse]:
    service = ComentarService(db)
    return await service.listar_comentarios_elemento(proyecto_id, elemento_id)


@router.get("/proyecto/{proyecto_id}", response_model=List[ComentarioResponse])
async def obtener_todos_comentarios_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector"))
) -> List[ComentarioResponse]:
    service = ComentarService(db)
    return await service.listar_todos_comentarios_proyecto(proyecto_id)


@router.patch("/{comentario_id}", response_model=ComentarioResponse)
async def actualizar_comentario(
    comentario_id: str,
    req: ActualizarComentarioRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido())
) -> ComentarioResponse:
    await _puede_tocar_comentario(db, usuario, comentario_id)
    service = ComentarService(db)
    return await service.actualizar_comentario(comentario_id, req)


@router.delete("/{comentario_id}")
async def eliminar_comentario(
    comentario_id: str,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido())
) -> dict:
    await _puede_tocar_comentario(db, usuario, comentario_id)
    service = ComentarService(db)
    return await service.eliminar_comentario(comentario_id)


async def _puede_tocar_comentario(db: AsyncSession, usuario, comentario_id: str) -> None:
    """Editar/resolver/borrar: su autor (siendo miembro) o un editor del proyecto."""
    c = (await db.execute(select(ComentarioElemento).where(ComentarioElemento.id == comentario_id))).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    nivel = await verificar_permiso(db, usuario, c.proyecto_id, "lector")
    if nivel == "lector" and c.autor_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo puedes modificar tus propios comentarios.")

