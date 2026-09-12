from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from backend.modules.gestion_modelado.models import DiagramElement, DiagramRelation
from backend.modules.gestion_modelado.editar_elemento.schemas.request import (
    EditarElementoRequest, EditarRelacionRequest
)

# Campos que cuentan como cambio semántico → suben versión
SEMANTIC_FIELDS_ELEMENTO = {"nombre", "color", "content"}
SEMANTIC_FIELDS_RELACION  = {"type", "label", "source_label", "target_label"}


async def editar_elemento(element_id: str, body: EditarElementoRequest, db: AsyncSession) -> DiagramElement:
    result = await db.execute(select(DiagramElement).where(DiagramElement.id == element_id))
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Elemento no encontrado.")

    incoming = body.model_dump(exclude_none=True)
    semantic_change = bool(SEMANTIC_FIELDS_ELEMENTO & incoming.keys())

    if "nombre"  in incoming: element.nombre  = body.nombre
    if "color"   in incoming: element.color   = body.color
    if "pos_x"   in incoming: element.pos_x   = body.pos_x
    if "pos_y"   in incoming: element.pos_y   = body.pos_y
    if "width"   in incoming: element.width   = body.width
    if "content" in incoming: element.content = body.content.model_dump()
    if "hash"    in incoming: element.hash    = body.hash

    if "version" in incoming:
        element.version = body.version
    elif semantic_change:
        element.version += 1

    await db.commit()
    await db.refresh(element)
    return element


async def editar_relacion(relation_id: str, body: EditarRelacionRequest, db: AsyncSession) -> DiagramRelation:
    result = await db.execute(select(DiagramRelation).where(DiagramRelation.id == relation_id))
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="Relación no encontrada.")

    incoming = body.model_dump(exclude_none=True)

    if "type"         in incoming: relation.type         = body.type
    if "label"        in incoming: relation.label        = body.label
    if "source_label" in incoming: relation.source_label = body.source_label
    if "target_label" in incoming: relation.target_label = body.target_label
    if "hash"         in incoming: relation.hash         = body.hash

    if "version" in incoming:
        relation.version = body.version
    else:
        relation.version += 1

    await db.commit()
    await db.refresh(relation)
    return relation
