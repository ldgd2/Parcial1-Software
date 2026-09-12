from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.core.database import get_db
from backend.modules.gestion_modelado.models import DiagramElement, DiagramRelation
from backend.modules.gestion_modelado.schemas import (
    CreateElementRequest, UpdateElementRequest, ElementResponse,
    CreateRelationRequest, UpdateRelationRequest, RelationResponse,
)
from typing import List

router = APIRouter(prefix="/modelado", tags=["Gestión de Modelado"])


# ──────────────────────────────────────────────────────────────────────────────
# CU8 — Insertar Elemento
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/elementos", response_model=ElementResponse, status_code=status.HTTP_201_CREATED,
             summary="CU8: Insertar elemento al diagrama")
async def insertar_elemento(body: CreateElementRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo elemento (clase, interfaz, enum, nota, etc.) en el diagrama.
    El ID es generado en el frontend para mantener coherencia con el estado local.
    """
    # Verificar que no exista ya
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


@router.get("/elementos/proyecto/{proyecto_id}", response_model=List[ElementResponse],
            summary="Obtener todos los elementos del diagrama de un proyecto")
async def listar_elementos(proyecto_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiagramElement).where(DiagramElement.proyecto_id == proyecto_id)
    )
    return result.scalars().all()


@router.get("/elementos/{element_id}", response_model=ElementResponse,
            summary="Obtener un elemento por ID")
async def obtener_elemento(element_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiagramElement).where(DiagramElement.id == element_id))
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Elemento no encontrado.")
    return element


# ──────────────────────────────────────────────────────────────────────────────
# CU10 — Editar Elemento
# ──────────────────────────────────────────────────────────────────────────────

@router.patch("/elementos/{element_id}", response_model=ElementResponse,
              summary="CU10: Editar un elemento del diagrama")
async def editar_elemento(element_id: str, body: UpdateElementRequest, db: AsyncSession = Depends(get_db)):
    """
    Edita propiedades de un elemento existente.
    Solo posición/dimensiones (pos_x, pos_y, width) se actualizan sin incrementar versión.
    Cambios de nombre, color o content sí incrementan la versión en el backend.
    """
    result = await db.execute(select(DiagramElement).where(DiagramElement.id == element_id))
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Elemento no encontrado.")

    # Detectar si hay cambios semánticos (no posición)
    semantic_change = any([
        body.nombre is not None and body.nombre != element.nombre,
        body.color is not None and body.color != element.color,
        body.content is not None,
    ])

    if body.nombre is not None:    element.nombre = body.nombre
    if body.color is not None:     element.color = body.color
    if body.pos_x is not None:     element.pos_x = body.pos_x
    if body.pos_y is not None:     element.pos_y = body.pos_y
    if body.width is not None:     element.width = body.width
    if body.content is not None:   element.content = body.content.model_dump()
    if body.hash is not None:      element.hash = body.hash

    # Si hay cambio semántico y no viene version explícita, auto-incrementar
    if semantic_change and body.version is None:
        element.version += 1
    elif body.version is not None:
        element.version = body.version

    await db.commit()
    await db.refresh(element)
    return element


# ──────────────────────────────────────────────────────────────────────────────
# CU11 — Eliminar Elemento
# ──────────────────────────────────────────────────────────────────────────────

@router.delete("/elementos/{element_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU11: Eliminar un elemento del diagrama")
async def eliminar_elemento(element_id: str, db: AsyncSession = Depends(get_db)):
    """
    Elimina un elemento. Las relaciones asociadas se eliminan en cascada.
    """
    result = await db.execute(select(DiagramElement).where(DiagramElement.id == element_id))
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Elemento no encontrado.")

    await db.delete(element)
    await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# CU9 — Conectar Elemento
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/relaciones", response_model=RelationResponse, status_code=status.HTTP_201_CREATED,
             summary="CU9: Conectar dos elementos con una relación")
async def crear_relacion(body: CreateRelationRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea una relación entre dos elementos del diagrama.
    Tipos: association, inheritance, composition, aggregation, dependency, realization, directed.
    """
    existing = await db.execute(select(DiagramRelation).where(DiagramRelation.id == body.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="La relación ya existe.")

    # Verificar que origen y destino existen
    src = await db.execute(select(DiagramElement).where(DiagramElement.id == body.source_id))
    tgt = await db.execute(select(DiagramElement).where(DiagramElement.id == body.target_id))
    if not src.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Elemento origen '{body.source_id}' no encontrado.")
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


@router.get("/relaciones/proyecto/{proyecto_id}", response_model=List[RelationResponse],
            summary="Obtener todas las relaciones de un proyecto")
async def listar_relaciones(proyecto_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiagramRelation).where(DiagramRelation.proyecto_id == proyecto_id)
    )
    return result.scalars().all()


@router.patch("/relaciones/{relation_id}", response_model=RelationResponse,
              summary="CU10: Editar una relación (label, multiplicidad, tipo)")
async def editar_relacion(relation_id: str, body: UpdateRelationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiagramRelation).where(DiagramRelation.id == relation_id))
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="Relación no encontrada.")

    if body.type is not None:         relation.type = body.type
    if body.label is not None:        relation.label = body.label
    if body.source_label is not None: relation.source_label = body.source_label
    if body.target_label is not None: relation.target_label = body.target_label
    if body.hash is not None:         relation.hash = body.hash
    if body.version is not None:
        relation.version = body.version
    else:
        relation.version += 1

    await db.commit()
    await db.refresh(relation)
    return relation


@router.delete("/relaciones/{relation_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU11: Eliminar una relación del diagrama")
async def eliminar_relacion(relation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiagramRelation).where(DiagramRelation.id == relation_id))
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="Relación no encontrada.")

    await db.delete(relation)
    await db.commit()
