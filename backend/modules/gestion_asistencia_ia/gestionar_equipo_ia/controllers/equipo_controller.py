from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user, get_current_user_optional
from backend.modules.gestion_usuarios.models import Usuario, TareaIA
from backend.modules.gestion_asistencia_ia.gestionar_equipo_ia.schemas.request import (
    GenerarEquipoRequest,
    TareaIAOut,
    ActualizarHabilidadesRequest,
)
from backend.modules.gestion_asistencia_ia.gestionar_equipo_ia.services.equipo_service import (
    generar_y_persistir_tareas,
    obtener_tareas_usuario,
    obtener_tareas_proyecto,
    marcar_tarea,
)

router = APIRouter(prefix="/api/ia/equipo", tags=["IA - Gestión de Equipo"])


from backend.modules.gestion_proyectos.models import Proyecto
from backend.core.websockets.connection_manager import manager

@router.post("/generar", response_model=List[TareaIAOut])
async def generar_tareas_equipo(
    req: GenerarEquipoRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> List[TareaIA]:
    nuevas_tareas = await generar_y_persistir_tareas(req, db)
    
    # Notificar por WebSocket a la sala para que refresquen tareas
    result = await db.execute(select(Proyecto).where(Proyecto.id == req.proyecto_id))
    proyecto = result.scalar_one_or_none()
    if proyecto and proyecto.codigo_acceso:
        await manager.broadcast_to_sala({"type": "tareas_actualizadas"}, proyecto.codigo_acceso)
        
    return nuevas_tareas


@router.get("/proyecto/{proyecto_id}/mis-tareas", response_model=List[TareaIAOut])
async def mis_tareas(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional),
) -> List[TareaIA]:
    if not current_user:
        return await obtener_tareas_proyecto(proyecto_id, db)

    tareas = await obtener_tareas_usuario(proyecto_id, current_user.id, db)
    if not tareas:
        return await obtener_tareas_proyecto(proyecto_id, db)

    return tareas
    return tareas


@router.get("/proyecto/{proyecto_id}/todas", response_model=List[TareaIAOut])
async def todas_las_tareas_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> List[TareaIA]:
    return await obtener_tareas_proyecto(proyecto_id, db)


@router.patch("/tarea/{tarea_id}/completar", response_model=TareaIAOut)
async def completar_tarea(
    tarea_id: int,
    completada: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional),
) -> TareaIA:
    uid = current_user.id if current_user else None
    return await marcar_tarea(tarea_id, uid, completada, db)


@router.put("/habilidades", response_model=dict)
async def actualizar_habilidades(
    body: ActualizarHabilidadesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional),
) -> dict:
    if not current_user:
        return {"ok": True, "etiquetas": body.etiquetas}

    result = await db.execute(select(Usuario).where(Usuario.id == current_user.id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.etiquetas_habilidades = body.etiquetas
    await db.commit()
    return {"ok": True, "etiquetas": body.etiquetas}
