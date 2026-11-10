"""Permiso de edición por proyecto (CU38 / CU43).

El anfitrión puede dejar a un colaborador como "Lector" desde Permisos de Acceso. Ese rol se
guarda en colaboradores_proyecto (permiso_rol / puede_editar) y TODO endpoint que modifica el
diagrama debe comprobarlo en el servidor: ocultar botones en el frontend no basta, porque un
lector puede llamar a la API directamente (CP51).
"""
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.gestion_proyectos.models import ColaboradorProyecto

MENSAJE_SOLO_LECTURA = "Tu permiso en este proyecto es de solo lectura. Pide al anfitrión que te asigne como editor."


def es_lector(colaborador: ColaboradorProyecto | None) -> bool:
    if colaborador is None or colaborador.rol_proyecto == "anfitrion":
        return False
    return colaborador.permiso_rol == "lector" or not colaborador.puede_editar


async def obtener_colaborador(db: AsyncSession, proyecto_id: int, usuario_id: int) -> ColaboradorProyecto | None:
    resultado = await db.execute(
        select(ColaboradorProyecto).where(
            ColaboradorProyecto.proyecto_id == proyecto_id,
            ColaboradorProyecto.usuario_id == usuario_id,
        )
    )
    return resultado.scalar_one_or_none()


async def exigir_permiso_edicion(db: AsyncSession, proyecto_id: int | None, usuario) -> None:
    """403 si el usuario es colaborador del proyecto con permiso de solo lectura."""
    usuario_id = getattr(usuario, "id", None)
    if not proyecto_id or not usuario_id:
        return
    if es_lector(await obtener_colaborador(db, proyecto_id, usuario_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_SOLO_LECTURA)


async def guardar_permiso(db: AsyncSession, proyecto_id: int, usuario_id: int, lector: bool) -> bool:
    """Persiste el rol elegido por el anfitrión. Devuelve False si el usuario no es colaborador."""
    resultado = await db.execute(
        update(ColaboradorProyecto)
        .where(
            ColaboradorProyecto.proyecto_id == proyecto_id,
            ColaboradorProyecto.usuario_id == usuario_id,
            ColaboradorProyecto.rol_proyecto != "anfitrion",
        )
        .values(
            permiso_rol="lector" if lector else "editor",
            puede_editar=not lector,
            puede_eliminar=not lector,
            puede_usar_ia=not lector,
        )
    )
    await db.commit()
    return resultado.rowcount > 0
