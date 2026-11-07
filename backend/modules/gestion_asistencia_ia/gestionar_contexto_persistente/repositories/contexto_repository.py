from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.modules.gestion_asistencia_ia.models import ContextoIAProyecto


class ContextoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_proyecto_id(self, proyecto_id: int) -> Optional[ContextoIAProyecto]:
        stmt = select(ContextoIAProyecto).where(ContextoIAProyecto.proyecto_id == proyecto_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_or_get(self, proyecto_id: int, dominio_inicial: str = "Sistema de Software") -> ContextoIAProyecto:
        existing = await self.get_by_proyecto_id(proyecto_id)
        if existing:
            return existing

        nuevo = ContextoIAProyecto(
            proyecto_id=proyecto_id,
            dominio=dominio_inicial,
            resumen_acumulado="",
            historial_comprimido=[],
            correcciones=[],
            snapshot_dsl="",
            tokens_ahorrados_estimados=0,
            version=1
        )
        self.db.add(nuevo)
        await self.db.commit()
        await self.db.refresh(nuevo)
        return nuevo

    async def update(self, contexto: ContextoIAProyecto) -> ContextoIAProyecto:
        contexto.version += 1
        await self.db.commit()
        await self.db.refresh(contexto)
        return contexto

    async def reset(self, proyecto_id: int, conservar_dominio: bool = True) -> Optional[ContextoIAProyecto]:
        contexto = await self.get_by_proyecto_id(proyecto_id)
        if not contexto:
            return None

        contexto.resumen_acumulado = ""
        contexto.historial_comprimido = []
        contexto.correcciones = []
        contexto.snapshot_dsl = ""
        if not conservar_dominio:
            contexto.dominio = "Sistema de Software"
        contexto.version += 1
        await self.db.commit()
        await self.db.refresh(contexto)
        return contexto

