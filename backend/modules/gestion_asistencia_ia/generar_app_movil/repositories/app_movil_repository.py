import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.modules.gestion_proyectos.models import Proyecto


async def obtener_diagrama_proyecto(proyecto_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar_one_or_none()
    if not proyecto or not proyecto.lienzo_json:
        return None
    try:
        data = json.loads(proyecto.lienzo_json)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def obtener_proyecto_nombre(proyecto_id: int, db: AsyncSession) -> str:
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar_one_or_none()
    if proyecto and proyecto.nombre:
        return proyecto.nombre
    return "app_movil"

