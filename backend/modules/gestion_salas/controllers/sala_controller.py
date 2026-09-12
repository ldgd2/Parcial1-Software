from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
from backend.core.websockets.connection_manager import manager

router = APIRouter(prefix="/salas", tags=["Gestion Salas"])


@router.get("/unirse/{codigo_acceso}")
async def unirse_sala(
    codigo_acceso: str,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CU7 - Unirse a Sala.
    Verifica el código de acceso, crea la solicitud si es nuevo colaborador,
    y retorna los datos del proyecto para cargar la sala.
    """
    result = await db.execute(
        select(Proyecto)
        .options(selectinload(Proyecto.colaboradores))
        .where(Proyecto.codigo_acceso == codigo_acceso)
    )
    proyecto = result.scalars().first()

    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de acceso inválido o proyecto no encontrado."
        )

    # Verificar si ya es colaborador
    colaborador = next(
        (c for c in proyecto.colaboradores if c.usuario_id == user.id), None
    )

    if not colaborador:
        # Crear solicitud pendiente
        nueva_solicitud = ColaboradorProyecto(
            proyecto_id=proyecto.id,
            usuario_id=user.id,
            rol_proyecto="invitado",
            estado="pendiente"
        )
        db.add(nueva_solicitud)
        await db.commit()
        
        # Notify the host that an authenticated user is waiting
        await manager.notify_host(proyecto.codigo_acceso, {
            "type": "join_request",
            "guest_id": f"auth_{user.id}",
            "nickname": user.nombre
        })
        
        return {
            "acceso": "pendiente",
            "mensaje": "Solicitud enviada al anfitrión. Espera su aprobación.",
            "proyecto_id": proyecto.id,
            "proyecto_nombre": proyecto.nombre
        }

    if colaborador.estado == "rechazado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu solicitud fue rechazada. Contacta al anfitrión del proyecto."
        )

    if colaborador.estado == "pendiente":
        # Re-notify the host in case they missed it or refreshed
        await manager.notify_host(proyecto.codigo_acceso, {
            "type": "join_request",
            "guest_id": f"auth_{user.id}",
            "nickname": user.nombre
        })
        return {
            "acceso": "pendiente",
            "mensaje": "Tu solicitud sigue pendiente de aprobación.",
            "proyecto_id": proyecto.id,
            "proyecto_nombre": proyecto.nombre
        }

    # Estado aprobado — acceso concedido
    return {
        "acceso": "aprobado",
        "proyecto_id": proyecto.id,
        "proyecto_nombre": proyecto.nombre,
        "codigo_acceso": proyecto.codigo_acceso,
        "lienzo_json": proyecto.lienzo_json
    }


@router.get("/{proyecto_id}/lienzo")
async def cargar_lienzo(
    proyecto_id: int,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CU8 - Cargar Lienzo.
    Retorna el estado actual del diagrama del proyecto.
    Solo colaboradores aprobados pueden acceder.
    """
    result = await db.execute(
        select(Proyecto)
        .options(selectinload(Proyecto.colaboradores))
        .where(Proyecto.id == proyecto_id)
    )
    proyecto = result.scalars().first()

    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    colaborador = next(
        (c for c in proyecto.colaboradores if c.usuario_id == user.id), None
    )
    if not colaborador or colaborador.estado != "aprobado":
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    return {
        "proyecto_id": proyecto.id,
        "proyecto_nombre": proyecto.nombre,
        "codigo_acceso": proyecto.codigo_acceso,
        "lienzo_json": proyecto.lienzo_json or "null",
        "rol_proyecto": colaborador.rol_proyecto
    }


@router.put("/{proyecto_id}/lienzo")
async def guardar_lienzo(
    proyecto_id: int,
    payload: dict,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CU8 - Guardar Lienzo.
    Persiste el estado del diagrama. Solo colaboradores aprobados.
    """
    import json

    result = await db.execute(
        select(Proyecto)
        .options(selectinload(Proyecto.colaboradores))
        .where(Proyecto.id == proyecto_id)
    )
    proyecto = result.scalars().first()

    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    colaborador = next(
        (c for c in proyecto.colaboradores if c.usuario_id == user.id), None
    )
    if not colaborador or colaborador.estado != "aprobado":
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    proyecto.lienzo_json = json.dumps(payload.get("lienzo"))
    await db.commit()

    return {"detail": "Lienzo guardado exitosamente."}
