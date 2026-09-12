from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.core.repository import BaseRepository
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto

class AdminProyectoRepository(BaseRepository):
    
    async def get_colaborador(self, db: AsyncSession, proyecto_id: int, usuario_id: int) -> ColaboradorProyecto | None:
        result = await db.execute(
            select(ColaboradorProyecto).where(
                ColaboradorProyecto.proyecto_id == proyecto_id,
                ColaboradorProyecto.usuario_id == usuario_id
            )
        )
        return result.scalars().first()
        
    async def get_solicitudes(self, db: AsyncSession, proyecto_id: int):
        result = await db.execute(
            select(ColaboradorProyecto)
            .options(selectinload(ColaboradorProyecto.usuario))
            .where(
                ColaboradorProyecto.proyecto_id == proyecto_id,
                ColaboradorProyecto.estado == "pendiente"
            )
        )
        return result.scalars().all()

    async def get_mis_proyectos(self, db: AsyncSession, usuario_id: int):
        """Retorna todos los proyectos donde el usuario es colaborador aprobado."""
        result = await db.execute(
            select(Proyecto)
            .join(ColaboradorProyecto, ColaboradorProyecto.proyecto_id == Proyecto.id)
            .where(
                ColaboradorProyecto.usuario_id == usuario_id,
                ColaboradorProyecto.estado == "aprobado"
            )
            .options(selectinload(Proyecto.colaboradores))
        )
        return result.scalars().all()

admin_repo = AdminProyectoRepository(Proyecto)
