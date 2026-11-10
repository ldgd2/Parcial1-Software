from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from backend.modules.gestion_usuarios.models import TareaIA


async def obtener_tareas_usuario(proyecto_id: int, usuario_id: int, db: AsyncSession) -> List[TareaIA]:
    result = await db.execute(
        select(TareaIA)
        .where((TareaIA.proyecto_id == proyecto_id) & (TareaIA.usuario_id == usuario_id))
        .order_by(TareaIA.orden, TareaIA.id)
    )
    return list(result.scalars().all())


async def obtener_todas_tareas_proyecto(proyecto_id: int, db: AsyncSession) -> List[TareaIA]:
    result = await db.execute(
        select(TareaIA)
        .where(TareaIA.proyecto_id == proyecto_id)
        .order_by(TareaIA.usuario_id, TareaIA.orden, TareaIA.id)
    )
    return list(result.scalars().all())


async def insertar_tareas(nuevas: List[TareaIA], db: AsyncSession) -> List[TareaIA]:
    for t in nuevas:
        db.add(t)
    await db.commit()
    for t in nuevas:
        await db.refresh(t)
    return nuevas


async def marcar_tarea_estado(tarea_id: int, completada: bool, db: AsyncSession) -> Optional[TareaIA]:
    result = await db.execute(select(TareaIA).where(TareaIA.id == tarea_id))
    tarea = result.scalar_one_or_none()
    if not tarea:
        return None
    tarea.completada = completada
    await db.commit()
    await db.refresh(tarea)
    return tarea


async def borrar_tarea(tarea_id: int, db: AsyncSession) -> bool:
    result = await db.execute(select(TareaIA).where(TareaIA.id == tarea_id))
    tarea = result.scalar_one_or_none()
    if not tarea:
        return False
    await db.delete(tarea)
    await db.commit()
    return True

