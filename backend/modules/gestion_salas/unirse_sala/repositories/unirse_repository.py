from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto


class UnirseSalaRepository:
    async def obtener_proyecto_por_codigo(
        self, db: AsyncSession, codigo_acceso: str
    ) -> Optional[Proyecto]:
        result = await db.execute(
            select(Proyecto)
            .options(selectinload(Proyecto.colaboradores))
            .where(Proyecto.codigo_acceso == codigo_acceso)
        )
        return result.scalars().first()

    async def crear_solicitud_colaborador(
        self, db: AsyncSession, proyecto_id: int, usuario_id: int
    ) -> ColaboradorProyecto:
        nueva_solicitud = ColaboradorProyecto(
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            rol_proyecto="invitado",
            estado="pendiente"
        )
        db.add(nueva_solicitud)
        await db.commit()
        return nueva_solicitud


unirse_sala_repository = UnirseSalaRepository()
