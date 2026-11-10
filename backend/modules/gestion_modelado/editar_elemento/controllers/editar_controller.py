from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from backend.modules.gestion_modelado.editar_elemento.schemas.request import (
    EditarElementoRequest, EditarRelacionRequest,
    ElementoResponse, RelacionResponse
)
from backend.modules.gestion_modelado.editar_elemento.services.editar_service import (
    editar_elemento, editar_relacion
)


router = APIRouter(tags=["CU10 - Editar Elemento"])


@router.patch("/modelado/elementos/{element_id}", response_model=ElementoResponse,
              summary="CU10: Editar un elemento del diagrama (semántico sube versión, posición no)")
async def cu10_editar_elemento(
    element_id: str,
    body: EditarElementoRequest,
    db: AsyncSession = Depends(get_db),
    usuario=Depends(usuario_requerido()),
):
    from backend.modules.gestion_modelado.models import DiagramElement
    await _permiso_por_id(db, usuario, DiagramElement, element_id, "editor")
    return await editar_elemento(element_id, body, db)


@router.patch("/modelado/relaciones/{relation_id}", response_model=RelacionResponse,
              summary="CU10: Editar una relación (etiqueta, tipo, multiplicidad)")
async def cu10_editar_relacion(
    relation_id: str,
    body: EditarRelacionRequest,
    db: AsyncSession = Depends(get_db),
    usuario=Depends(usuario_requerido()),
):
    from backend.modules.gestion_modelado.models import DiagramRelation
    await _permiso_por_id(db, usuario, DiagramRelation, relation_id, "editor")
    return await editar_relacion(relation_id, body, db)


@router.get("/modelado/elementos/{element_id}", response_model=ElementoResponse,
            summary="Obtener un elemento por ID")
async def cu10_get_elemento(element_id: str, db: AsyncSession = Depends(get_db), usuario=Depends(usuario_requerido())):
    from sqlalchemy import select
    from backend.modules.gestion_modelado.models import DiagramElement
    from fastapi import HTTPException
    result = await db.execute(select(DiagramElement).where(DiagramElement.id == element_id))
    el = result.scalar_one_or_none()
    if not el:
        raise HTTPException(status_code=404, detail="Elemento no encontrado.")
    await verificar_permiso(db, usuario, el.proyecto_id, "lector")
    return el


async def _permiso_por_id(db, usuario, modelo, objeto_id: str, nivel: str):
    """Valida el permiso en el proyecto del elemento/relación (404 si no existe)."""
    from fastapi import HTTPException
    obj = await db.get(modelo, objeto_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="No encontrado.")
    await verificar_permiso(db, usuario, obj.proyecto_id, nivel)

