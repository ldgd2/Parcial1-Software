import json
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.modules.gestion_proyectos.models import Proyecto


class GuardarLienzoRepository:
    async def obtener_proyecto_con_colaboradores(
        self, db: AsyncSession, proyecto_id: int
    ) -> Optional[Proyecto]:
        result = await db.execute(
            select(Proyecto)
            .options(selectinload(Proyecto.colaboradores))
            .where(Proyecto.id == proyecto_id)
        )
        return result.scalars().first()

    async def guardar_lienzo_proyecto(
        self, db: AsyncSession, proyecto: Proyecto, lienzo: Any
    ) -> None:
        proyecto.lienzo_json = json.dumps(lienzo)
        await db.commit()


guardar_lienzo_repository = GuardarLienzoRepository()
