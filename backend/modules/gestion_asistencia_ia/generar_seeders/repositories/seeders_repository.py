import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.modules.gestion_proyectos.models import Proyecto


class SeedersRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_diagrama_por_proyecto_id(self, proyecto_id: int) -> Optional[Dict[str, Any]]:
        result = await self.db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalars().first()
        if not proyecto or not proyecto.lienzo_json:
            return None

        if isinstance(proyecto.lienzo_json, dict):
            return proyecto.lienzo_json

        try:
            parsed = json.loads(proyecto.lienzo_json)
            if isinstance(parsed, dict):
                return parsed
            return None
        except Exception:
            return None

