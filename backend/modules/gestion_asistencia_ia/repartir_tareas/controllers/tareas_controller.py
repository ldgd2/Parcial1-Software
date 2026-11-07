from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from backend.modules.gestion_asistencia_ia.repartir_tareas.schemas.request import (
    RepartirTareasRequest,
    CrearTareaRequest,
)
from backend.modules.gestion_asistencia_ia.repartir_tareas.schemas.response import (
    TareaResponse,
    RepartirTareasResponse,
)
from backend.modules.gestion_asistencia_ia.repartir_tareas.services.tareas_service import (
    ejecutar_reparticion_tareas,
    listar_mis_tareas,
    listar_todas_tareas,
    cambiar_estado_tarea,
    registrar_tarea_manual,
    suprimir_tarea,
)

router = APIRouter(prefix="/api/ia/tareas", tags=["IA - Repartición de Tareas"])


@router.post("/repartir", response_model=RepartirTareasResponse)
async def repartir_tareas(
    req: RepartirTareasRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> RepartirTareasResponse:
    return await ejecutar_reparticion_tareas(req, db)


@router.get("/proyecto/{proyecto_id}/mis-tareas", response_model=List[TareaResponse])
async def obtener_mis_tareas(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
) -> List[TareaResponse]:
    uid = current_user.id if current_user else None
    return await listar_mis_tareas(proyecto_id, uid, db)


@router.get("/proyecto/{proyecto_id}/todas", response_model=List[TareaResponse])
async def obtener_todas_las_tareas(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> List[TareaResponse]:
    return await listar_todas_tareas(proyecto_id, db)


@router.patch("/{tarea_id}/completar", response_model=TareaResponse)
async def marcar_tarea(
    tarea_id: int,
    completada: bool = True,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> TareaResponse:
    return await cambiar_estado_tarea(tarea_id, completada, db)


@router.post("/crear", response_model=TareaResponse)
async def crear_tarea_manual(
    req: CrearTareaRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> TareaResponse:
    return await registrar_tarea_manual(req, db)


@router.delete("/{tarea_id}", response_model=dict)
async def eliminar_tarea(
    tarea_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> dict:
    return await suprimir_tarea(tarea_id, db)

