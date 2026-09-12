from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_modelado.eliminar_elemento.services.eliminar_service import (
    eliminar_elemento, eliminar_relacion
)

router = APIRouter(tags=["CU11 - Eliminar Elemento"])


@router.delete("/modelado/elementos/{element_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU11: Eliminar un elemento del diagrama (las relaciones se eliminan en cascada)")
async def cu11_eliminar_elemento(element_id: str, db: AsyncSession = Depends(get_db)):
    await eliminar_elemento(element_id, db)


@router.delete("/modelado/relaciones/{relation_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU11: Eliminar una relación del diagrama")
async def cu11_eliminar_relacion(relation_id: str, db: AsyncSession = Depends(get_db)):
    await eliminar_relacion(relation_id, db)
