from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.core.repository import BaseRepository
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
from backend.modules.gestion_proyectos.crear_proyecto.schemas.request import ProyectoCreate

class ProyectoRepository(BaseRepository):
    
    async def crear_con_anfitrion(self, db: AsyncSession, data: ProyectoCreate, usuario_id: int) -> Proyecto:
        db_proyecto = Proyecto(nombre=data.nombre, descripcion=data.descripcion)
        db.add(db_proyecto)
        await db.flush()  # Flush para obtener el ID generado
        
        # El creador es anfitrión y ya está aprobado automáticamente
        colaborador = ColaboradorProyecto(
            proyecto_id=db_proyecto.id,
            usuario_id=usuario_id,
            rol_proyecto="anfitrion",
            estado="aprobado"
        )
        db.add(colaborador)
        await db.commit()
        
        # Re-fetch con selectinload para evitar MissingGreenlet durante serialización
        result = await db.execute(
            select(Proyecto)
            .options(selectinload(Proyecto.colaboradores))
            .where(Proyecto.id == db_proyecto.id)
        )
        return result.scalars().first()

proyecto_repo = ProyectoRepository(Proyecto)
