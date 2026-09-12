from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.core.database import get_db
from backend.modules.gestion_modelado.conectar_elemento.schemas.request import (
    ConectarElementoRequest, RelacionResponse
)
from backend.modules.gestion_modelado.conectar_elemento.services.conectar_service import (
    conectar_elemento, listar_relaciones
)

router = APIRouter(prefix="/modelado/relaciones", tags=["CU9 - Conectar Elemento"])


@router.post("", response_model=RelacionResponse, status_code=status.HTTP_201_CREATED,
             summary="CU9: Crear una relación entre dos elementos del diagrama")
async def cu9_conectar(body: ConectarElementoRequest, db: AsyncSession = Depends(get_db)):
    return await conectar_elemento(body, db)


@router.get("/proyecto/{proyecto_id}", response_model=List[RelacionResponse],
            summary="Listar todas las relaciones de un proyecto")
async def cu9_listar(proyecto_id: int, db: AsyncSession = Depends(get_db)):
    return await listar_relaciones(proyecto_id, db)
