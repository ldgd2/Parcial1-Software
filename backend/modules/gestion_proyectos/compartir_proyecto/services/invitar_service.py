"""
CU08 / CU38: compartir un proyecto por correo con un permiso y administrar los permisos de los miembros.

Antes solo existía el enlace de invitación (el invitado quedaba "pendiente" y como editor) y el rol
Lector se cambiaba únicamente por WebSocket, sin un endpoint que el servidor pudiera validar.
"""
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.permissions.proyecto import guardar_permiso, obtener_colaborador
from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.models import Usuario

SOLO_ANFITRION = "Solo el anfitrión del proyecto puede hacer esto."
PERMISOS = ("editor", "lector")


async def _exigir_anfitrion(db: AsyncSession, proyecto_id: int, usuario_id: int) -> Proyecto:
    proyecto = await db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
    colaborador = await obtener_colaborador(db, proyecto_id, usuario_id)
    if not colaborador or colaborador.rol_proyecto != "anfitrion" or colaborador.estado != "aprobado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SOLO_ANFITRION)
    return proyecto


def _validar_permiso(permiso: str) -> str:
    permiso = (permiso or "").strip().lower()
    if permiso not in PERMISOS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El permiso debe ser “editor” o “lector”.")
    return permiso


def _miembro(colaborador: ColaboradorProyecto, usuario: Usuario) -> dict:
    return {
        "usuario_id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol_proyecto": colaborador.rol_proyecto,
        "estado": colaborador.estado,
        "permiso": "anfitrion" if colaborador.rol_proyecto == "anfitrion" else (colaborador.permiso_rol or "editor"),
    }


async def _avisar_sala(proyecto: Proyecto, usuario_id: int, lector: bool) -> None:
    """Si el miembro está conectado a la sala, el cambio de permiso se aplica sin recargar."""
    from backend.modules.gestion_concurrencia.sincronizacion_tiempo_real.controllers.ws_sync_controller import (
        aplicar_rol_en_vivo,
    )
    await aplicar_rol_en_vivo(proyecto.codigo_acceso, usuario_id, lector)


async def invitar_por_correo(db: AsyncSession, proyecto_id: int, email: str, permiso: str, anfitrion: Usuario) -> dict:
    proyecto = await _exigir_anfitrion(db, proyecto_id, anfitrion.id)
    permiso = _validar_permiso(permiso)
    email = (email or "").strip().lower()

    invitado = (await db.execute(select(Usuario).where(func.lower(Usuario.email) == email))).scalar_one_or_none()
    if invitado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay ninguna cuenta con el correo {email}. El invitado primero debe registrarse en la plataforma.",
        )
    if invitado.id == anfitrion.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya eres el anfitrión de este proyecto.")

    colaborador = await obtener_colaborador(db, proyecto_id, invitado.id)
    if colaborador and colaborador.rol_proyecto == "anfitrion":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese usuario ya es anfitrión del proyecto.")

    lector = permiso == "lector"
    if colaborador is None:
        colaborador = ColaboradorProyecto(
            proyecto_id=proyecto_id, usuario_id=invitado.id, rol_proyecto="invitado", estado="aprobado",
            permiso_rol=permiso, puede_editar=not lector, puede_eliminar=not lector, puede_usar_ia=not lector,
        )
        db.add(colaborador)
    else:
        # Ya había pedido entrar con el enlace (o estaba rechazado): la invitación lo aprueba
        colaborador.estado = "aprobado"
        colaborador.permiso_rol = permiso
        colaborador.puede_editar = colaborador.puede_eliminar = colaborador.puede_usar_ia = not lector
    await db.commit()
    await _avisar_sala(proyecto, invitado.id, lector)
    return _miembro(colaborador, invitado)


async def listar_miembros(db: AsyncSession, proyecto_id: int, usuario: Usuario) -> list[dict]:
    colaborador = await obtener_colaborador(db, proyecto_id, usuario.id)
    if not colaborador or colaborador.estado != "aprobado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No eres miembro de este proyecto.")
    filas = (await db.execute(
        select(ColaboradorProyecto, Usuario)
        .join(Usuario, Usuario.id == ColaboradorProyecto.usuario_id)
        .where(ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.estado == "aprobado")
        .order_by(ColaboradorProyecto.rol_proyecto, Usuario.nombre)
    )).all()
    return [_miembro(c, u) for c, u in filas]


async def cambiar_permiso(db: AsyncSession, proyecto_id: int, usuario_id: int, permiso: str, anfitrion: Usuario) -> dict:
    proyecto = await _exigir_anfitrion(db, proyecto_id, anfitrion.id)
    permiso = _validar_permiso(permiso)
    colaborador = await obtener_colaborador(db, proyecto_id, usuario_id)
    if colaborador is None or colaborador.estado != "aprobado":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ese usuario no es miembro del proyecto.")
    if colaborador.rol_proyecto == "anfitrion":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cambiar el permiso del anfitrión.")
    lector = permiso == "lector"
    await guardar_permiso(db, proyecto_id, usuario_id, lector)
    await _avisar_sala(proyecto, usuario_id, lector)
    await db.refresh(colaborador)
    return _miembro(colaborador, await db.get(Usuario, usuario_id))


async def compartidos_conmigo(db: AsyncSession, usuario: Usuario) -> list[Proyecto]:
    """Proyectos donde el usuario es invitado aprobado (no los que creó)."""
    resultado = await db.execute(
        select(Proyecto)
        .join(ColaboradorProyecto, ColaboradorProyecto.proyecto_id == Proyecto.id)
        .where(
            ColaboradorProyecto.usuario_id == usuario.id,
            ColaboradorProyecto.estado == "aprobado",
            ColaboradorProyecto.rol_proyecto != "anfitrion",
        )
        .options(selectinload(Proyecto.colaboradores))
        .order_by(Proyecto.id.desc())
    )
    return list(resultado.scalars().all())
