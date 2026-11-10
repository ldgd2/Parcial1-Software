from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from backend.modules.gestion_modelado.eliminar_elemento.services.eliminar_service import (
    eliminar_elemento, eliminar_relacion
)


router = APIRouter(tags=["CU11 - Eliminar Elemento"])


@router.delete("/modelado/elementos/{element_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU11: Eliminar un elemento del diagrama (las relaciones se eliminan en cascada)")
async def cu11_eliminar_elemento(element_id: str, db: AsyncSession = Depends(get_db), usuario=Depends(usuario_requerido())):
    from backend.modules.gestion_modelado.models import DiagramElement
    await _permiso_por_id(db, usuario, DiagramElement, element_id, "editor")
    await eliminar_elemento(element_id, db)


@router.delete("/modelado/relaciones/{relation_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU11: Eliminar una relación del diagrama")
async def cu11_eliminar_relacion(relation_id: str, db: AsyncSession = Depends(get_db), usuario=Depends(usuario_requerido())):
    from backend.modules.gestion_modelado.models import DiagramRelation
    await _permiso_por_id(db, usuario, DiagramRelation, relation_id, "editor")
    await eliminar_relacion(relation_id, db)


async def _permiso_por_id(db, usuario, modelo, objeto_id: str, nivel: str):
    """Valida el permiso en el proyecto del elemento/relación (404 si no existe)."""
    from fastapi import HTTPException
    obj = await db.get(modelo, objeto_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="No encontrado.")
    await verificar_permiso(db, usuario, obj.proyecto_id, nivel)

