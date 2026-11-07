from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..repositories.comentar_repository import ComentarRepository
from ..schemas.request import CrearComentarioRequest, ActualizarComentarioRequest
from ..schemas.response import ComentarioResponse


class ComentarService:
    def __init__(self, db: AsyncSession):
        self.repo = ComentarRepository(db)

    async def agregar_comentario(
        self,
        req: CrearComentarioRequest,
        autor_id: Optional[int] = None,
        autor_nombre: Optional[str] = None
    ) -> ComentarioResponse:
        nombre_final = autor_nombre or req.autor_nombre or "Colaborador"
        comentario = await self.repo.create(
            proyecto_id=req.proyecto_id,
            elemento_id=req.elemento_id,
            elemento_tipo=req.elemento_tipo,
            texto=req.texto,
            autor_id=autor_id,
            autor_nombre=nombre_final
        )
        return self._to_response(comentario)

    async def listar_comentarios_elemento(
        self,
        proyecto_id: int,
        elemento_id: str
    ) -> List[ComentarioResponse]:
        comentarios = await self.repo.list_by_elemento(proyecto_id, elemento_id)
        return [self._to_response(c) for c in comentarios]

    async def listar_todos_comentarios_proyecto(
        self,
        proyecto_id: int
    ) -> List[ComentarioResponse]:
        comentarios = await self.repo.list_by_proyecto(proyecto_id)
        return [self._to_response(c) for c in comentarios]

    async def actualizar_comentario(
        self,
        comentario_id: str,
        req: ActualizarComentarioRequest
    ) -> ComentarioResponse:
        comentario = await self.repo.get_by_id(comentario_id)
        if not comentario:
            raise HTTPException(status_code=404, detail="Comentario no encontrado")

        if req.texto is not None:
            comentario.texto = req.texto
        if req.estado is not None:
            if req.estado not in ["abierto", "resuelto"]:
                raise HTTPException(status_code=400, detail="Estado inválido. Debe ser 'abierto' o 'resuelto'")
            comentario.estado = req.estado

        actualizado = await self.repo.update(comentario)
        return self._to_response(actualizado)

    async def eliminar_comentario(self, comentario_id: str) -> dict:
        comentario = await self.repo.get_by_id(comentario_id)
        if not comentario:
            raise HTTPException(status_code=404, detail="Comentario no encontrado")
        await self.repo.delete(comentario_id)
        return {"ok": True, "message": "Comentario eliminado exitosamente"}

    def _to_response(self, c) -> ComentarioResponse:
        return ComentarioResponse(
            id=c.id,
            proyecto_id=c.proyecto_id,
            elemento_id=c.elemento_id,
            elemento_tipo=c.elemento_tipo,
            autor_id=c.autor_id,
            autor_nombre=c.autor_nombre,
            texto=c.texto,
            estado=c.estado,
            created_at=c.created_at.isoformat() if c.created_at else "",
            updated_at=c.updated_at.isoformat() if c.updated_at else ""
        )

