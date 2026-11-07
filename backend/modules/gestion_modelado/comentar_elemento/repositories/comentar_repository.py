import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.modules.gestion_modelado.models import ComentarioElemento


class ComentarRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        proyecto_id: int,
        elemento_id: str,
        elemento_tipo: str,
        texto: str,
        autor_id: Optional[int] = None,
        autor_nombre: str = "Colaborador"
    ) -> ComentarioElemento:
        nuevo = ComentarioElemento(
            id=f"comm_{uuid.uuid4().hex[:12]}",
            proyecto_id=proyecto_id,
            elemento_id=elemento_id,
            elemento_tipo=elemento_tipo,
            autor_id=autor_id,
            autor_nombre=autor_nombre,
            texto=texto,
            estado="abierto"
        )
        self.db.add(nuevo)
        await self.db.commit()
        await self.db.refresh(nuevo)
        return nuevo

    async def get_by_id(self, comentario_id: str) -> Optional[ComentarioElemento]:
        stmt = select(ComentarioElemento).where(ComentarioElemento.id == comentario_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_by_elemento(self, proyecto_id: int, elemento_id: str) -> List[ComentarioElemento]:
        stmt = (
            select(ComentarioElemento)
            .where(
                ComentarioElemento.proyecto_id == proyecto_id,
                ComentarioElemento.elemento_id == elemento_id
            )
            .order_by(ComentarioElemento.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_by_proyecto(self, proyecto_id: int) -> List[ComentarioElemento]:
        stmt = (
            select(ComentarioElemento)
            .where(ComentarioElemento.proyecto_id == proyecto_id)
            .order_by(ComentarioElemento.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update(self, comentario: ComentarioElemento) -> ComentarioElemento:
        await self.db.commit()
        await self.db.refresh(comentario)
        return comentario

    async def delete(self, comentario_id: str) -> bool:
        stmt = delete(ComentarioElemento).where(ComentarioElemento.id == comentario_id)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount > 0

