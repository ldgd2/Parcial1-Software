from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from backend.core.database import get_db
from backend.core.auth import get_current_user
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


@router.post("/generar", response_model=List[TareaIAOut])
async def generar_tareas_equipo(
    req: GenerarEquipoRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> List[TareaIA]:
    return await generar_y_persistir_tareas(req, db)


@router.get("/proyecto/{proyecto_id}/mis-tareas", response_model=List[TareaIAOut])
async def mis_tareas(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> List[TareaIA]:
    return await obtener_tareas_usuario(proyecto_id, current_user.id, db)


@router.get("/proyecto/{proyecto_id}/todas", response_model=List[TareaIAOut])
async def todas_las_tareas_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> List[TareaIA]:
    return await obtener_tareas_proyecto(proyecto_id, db)


@router.patch("/tarea/{tarea_id}/completar", response_model=TareaIAOut)
async def completar_tarea(
    tarea_id: int,
    completada: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> TareaIA:
    return await marcar_tarea(tarea_id, current_user.id, completada, db)


@router.put("/habilidades", response_model=dict)
async def actualizar_habilidades(
    body: ActualizarHabilidadesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(Usuario).where(Usuario.id == current_user.id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.etiquetas_habilidades = body.etiquetas
    await db.commit()
    return {"ok": True, "etiquetas": body.etiquetas}
