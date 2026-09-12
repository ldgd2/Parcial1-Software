from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from backend.modules.gestion_modelado.models import DiagramElement, DiagramRelation


async def eliminar_elemento(element_id: str, db: AsyncSession) -> None:
    result = await db.execute(select(DiagramElement).where(DiagramElement.id == element_id))
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Elemento no encontrado.")
    await db.delete(element)
    await db.commit()


async def eliminar_relacion(relation_id: str, db: AsyncSession) -> None:
    result = await db.execute(select(DiagramRelation).where(DiagramRelation.id == relation_id))
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="Relación no encontrada.")
    await db.delete(relation)
    await db.commit()
