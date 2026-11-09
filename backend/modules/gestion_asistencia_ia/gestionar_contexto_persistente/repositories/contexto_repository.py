from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from backend.modules.gestion_asistencia_ia.models import ContextoIAProyecto, VersionContextoIA


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

    # ─── Versiones (antes/después de cada interacción de la IA) ─────────────

    async def agregar_version(self, **campos: Any) -> VersionContextoIA:
        """Agrega la versión sin confirmar: se guarda en el mismo commit que `update()`."""
        version = VersionContextoIA(**campos)
        self.db.add(version)
        await self.db.flush()  # asigna el id
        return version

    async def crear_version(self, **campos: Any) -> VersionContextoIA:
        version = VersionContextoIA(**campos)
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def listar_versiones(
        self, proyecto_id: int, limite: int, antes_de_id: Optional[int] = None
    ) -> List[VersionContextoIA]:
        """Más recientes primero. Pide `limite + 1` para saber si hay más páginas."""
        stmt = select(VersionContextoIA).where(VersionContextoIA.proyecto_id == proyecto_id)
        if antes_de_id is not None:
            stmt = stmt.where(VersionContextoIA.id < antes_de_id)
        stmt = stmt.order_by(VersionContextoIA.id.desc()).limit(limite + 1)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def obtener_version(self, proyecto_id: int, version_id: int) -> Optional[VersionContextoIA]:
        stmt = select(VersionContextoIA).where(
            VersionContextoIA.id == version_id,
            VersionContextoIA.proyecto_id == proyecto_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def decidir_propuesta(
        self,
        proyecto_id: int,
        version_id: int,
        estado: str,
        por: Optional[str],
        por_id: Optional[int],
        estado_antes: Optional[Dict[str, Any]],
    ) -> Optional[VersionContextoIA]:
        """
        Aprueba o rechaza una propuesta solo si sigue pendiente (una sola sentencia,
        así dos personas no pueden decidir la misma propuesta). None si ya estaba decidida.
        """
        valores: Dict[str, Any] = dict(
            estado_propuesta=estado, decidida_por=por, decidida_por_id=por_id, decidida_en=func.now()
        )
        if estado_antes is not None:
            valores["estado_antes"] = estado_antes
        stmt = (
            update(VersionContextoIA)
            .where(
                VersionContextoIA.id == version_id,
                VersionContextoIA.proyecto_id == proyecto_id,
                VersionContextoIA.estado_propuesta == "pendiente",
            )
            .values(**valores)
            .returning(VersionContextoIA.id)
            .execution_options(synchronize_session=False)
        )
        result = await self.db.execute(stmt)
        cambiada = result.scalar_one_or_none()
        await self.db.commit()
        if cambiada is None:
            return None
        version = await self.obtener_version(proyecto_id, version_id)
        if version is not None:
            await self.db.refresh(version)
        return version

    async def guardar_despues(self, version: VersionContextoIA, estado: Dict[str, Any]) -> VersionContextoIA:
        version.estado_despues = estado
        await self.db.commit()
        await self.db.refresh(version)
        return version
