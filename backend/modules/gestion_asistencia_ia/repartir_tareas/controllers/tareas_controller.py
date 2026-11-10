from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
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


router = APIRouter(prefix="/api/ia/tareas", tags=["Gestión de Asistencia IA - Repartición de Tareas"])


@router.post("/repartir", response_model=RepartirTareasResponse)
async def repartir_tareas(
    req: RepartirTareasRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> RepartirTareasResponse:
    await verificar_permiso(db, usuario, req.proyecto_id, "editor")
    return await ejecutar_reparticion_tareas(req, db)


@router.get("/proyecto/{proyecto_id}/mis-tareas", response_model=List[TareaResponse])
async def obtener_mis_tareas(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requiere_proyecto("lector")),
) -> List[TareaResponse]:
    uid = current_user.id if current_user else None
    return await listar_mis_tareas(proyecto_id, uid, db)


@router.get("/proyecto/{proyecto_id}/todas", response_model=List[TareaResponse])
async def obtener_todas_las_tareas(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> List[TareaResponse]:
    return await listar_todas_tareas(proyecto_id, db)


@router.patch("/{tarea_id}/completar", response_model=TareaResponse)
async def marcar_tarea(
    tarea_id: int,
    completada: bool = True,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> TareaResponse:
    await _tarea_y_permiso(db, usuario, tarea_id, "propia")
    tarea = await cambiar_estado_tarea(tarea_id, completada, db)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea


@router.post("/crear", response_model=TareaResponse)
async def crear_tarea_manual(
    req: CrearTareaRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> TareaResponse:
    # Lo usa también la aprobación de tareas propuestas por la IA → editor
    await verificar_permiso(db, usuario, req.proyecto_id, "editor")
    return await registrar_tarea_manual(req, db)


@router.delete("/{tarea_id}")
async def eliminar_tarea(
    tarea_id: int,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
):
    await _tarea_y_permiso(db, usuario, tarea_id, "editor")
    exito = await suprimir_tarea(tarea_id, db)
    if not exito:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"ok": True, "eliminada": tarea_id}


async def _tarea_y_permiso(db: AsyncSession, usuario, tarea_id: int, nivel: str):
    """Carga la tarea y valida el permiso en su proyecto. Completar la propia basta con ser miembro."""
    from backend.modules.gestion_usuarios.models import TareaIA
    tarea = await db.get(TareaIA, tarea_id)
    if tarea is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if nivel == "propia":
        actual = await verificar_permiso(db, usuario, tarea.proyecto_id, "lector")
        if actual == "lector" and tarea.usuario_id != usuario.id:
            raise HTTPException(status_code=403, detail="Solo puedes marcar tus propias tareas.")
    else:
        await verificar_permiso(db, usuario, tarea.proyecto_id, nivel)
    return tarea
