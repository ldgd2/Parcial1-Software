from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.core.database import get_db
from backend.modules.gestion_modelado.insertar_elemento.schemas.request import (
    InsertarElementoRequest, ElementoResponse
)
from backend.modules.gestion_modelado.insertar_elemento.services.insertar_service import (
    insertar_elemento, listar_elementos
)

router = APIRouter(prefix="/modelado/elementos", tags=["CU8 - Insertar Elemento"])


@router.post("", response_model=ElementoResponse, status_code=status.HTTP_201_CREATED,
             summary="CU8: Insertar un nuevo elemento al diagrama")
async def cu8_insertar(body: InsertarElementoRequest, db: AsyncSession = Depends(get_db)):
    return await insertar_elemento(body, db)


@router.get("/proyecto/{proyecto_id}", response_model=List[ElementoResponse],
            summary="Listar todos los elementos del diagrama de un proyecto")
async def cu8_listar(proyecto_id: int, db: AsyncSession = Depends(get_db)):
    return await listar_elementos(proyecto_id, db)
