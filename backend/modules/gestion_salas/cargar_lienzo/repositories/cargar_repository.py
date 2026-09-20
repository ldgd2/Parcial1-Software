from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.modules.gestion_proyectos.models import Proyecto


class CargarLienzoRepository:
    async def obtener_proyecto_con_colaboradores(
        self, db: AsyncSession, proyecto_id: int
    ) -> Optional[Proyecto]:
        result = await db.execute(
            select(Proyecto)
            .options(selectinload(Proyecto.colaboradores))
            .where(Proyecto.id == proyecto_id)
        )
        return result.scalars().first()


cargar_lienzo_repository = CargarLienzoRepository()
