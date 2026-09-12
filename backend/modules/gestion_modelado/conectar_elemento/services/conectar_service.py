from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from backend.modules.gestion_modelado.models import DiagramElement, DiagramRelation
from backend.modules.gestion_modelado.conectar_elemento.schemas.request import ConectarElementoRequest


async def conectar_elemento(body: ConectarElementoRequest, db: AsyncSession) -> DiagramRelation:
    existing = await db.execute(select(DiagramRelation).where(DiagramRelation.id == body.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="La relación ya existe.")

    src = await db.execute(select(DiagramElement).where(DiagramElement.id == body.source_id))
    if not src.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Elemento origen '{body.source_id}' no encontrado.")

    tgt = await db.execute(select(DiagramElement).where(DiagramElement.id == body.target_id))
    if not tgt.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Elemento destino '{body.target_id}' no encontrado.")

    relation = DiagramRelation(
        id=body.id,
        proyecto_id=body.proyecto_id,
        type=body.type,
        source_id=body.source_id,
        target_id=body.target_id,
        label=body.label,
        source_label=body.source_label,
        target_label=body.target_label,
        version=body.version,
        hash=body.hash,
    )
    db.add(relation)
    await db.commit()
    await db.refresh(relation)
    return relation


async def listar_relaciones(proyecto_id: int, db: AsyncSession) -> list[DiagramRelation]:
    result = await db.execute(
        select(DiagramRelation).where(DiagramRelation.proyecto_id == proyecto_id)
    )
    return list(result.scalars().all())
