from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.repository import BaseRepository
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
from backend.modules.gestion_proyectos.administrar_proyecto.repositories.admin_repo import admin_repo

class CompartirRepository(BaseRepository):
    
    async def get_proyecto_by_codigo(self, db: AsyncSession, codigo_acceso: str) -> Proyecto | None:
        result = await db.execute(select(Proyecto).where(Proyecto.codigo_acceso == codigo_acceso))
        return result.scalars().first()
        
    async def solicitar_unirse(self, db: AsyncSession, proyecto_id: int, usuario_id: int) -> ColaboradorProyecto:
        # Verificar si ya existe para evitar duplicados
        existente = await admin_repo.get_colaborador(db, proyecto_id, usuario_id)
        if existente:
            return existente
            
        nuevo_colaborador = ColaboradorProyecto(
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            rol_proyecto="invitado",
            estado="pendiente"
        )
        db.add(nuevo_colaborador)
        await db.commit()
        await db.refresh(nuevo_colaborador)
        return nuevo_colaborador

compartir_repo = CompartirRepository(Proyecto)
