from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.modules.gestion_modelado.models import DiagramElement
from backend.modules.gestion_modelado.insertar_elemento.schemas.request import InsertarElementoRequest
from fastapi import HTTPException


async def insertar_elemento(body: InsertarElementoRequest, db: AsyncSession) -> DiagramElement:
    existing = await db.execute(select(DiagramElement).where(DiagramElement.id == body.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El elemento ya existe.")

    element = DiagramElement(
        id=body.id,
        proyecto_id=body.proyecto_id,
        type=body.type,
        nombre=body.nombre,
        color=body.color,
        pos_x=body.pos_x,
        pos_y=body.pos_y,
        width=body.width,
        content=body.content.model_dump(),
        version=body.version,
        hash=body.hash,
    )
    db.add(element)
    await db.commit()
    await db.refresh(element)
    return element


async def listar_elementos(proyecto_id: int, db: AsyncSession) -> list[DiagramElement]:
    result = await db.execute(
        select(DiagramElement).where(DiagramElement.proyecto_id == proyecto_id)
    )
    return list(result.scalars().all())
