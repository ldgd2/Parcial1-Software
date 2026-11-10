"""CU38: permisos persistentes por colaborador (editor / lector) y su efecto en la sala en vivo."""
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.permissions.proyecto import PERMISOS_VALIDOS, nivel_de
from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.models import Usuario


async def listar_miembros(db: AsyncSession, proyecto_id: int) -> List[Dict[str, Any]]:
    filas = (await db.execute(
        select(ColaboradorProyecto, Usuario.nombre)
        .join(Usuario, Usuario.id == ColaboradorProyecto.usuario_id)
        .where(ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.estado == "aprobado")
        .order_by(ColaboradorProyecto.rol_proyecto.desc(), Usuario.nombre)
    )).all()
    return [{
        "usuario_id": c.usuario_id,
        "nombre": nombre,
        "rol_proyecto": c.rol_proyecto,
        "permiso": "edit" if c.rol_proyecto == "anfitrion" else (c.permiso or "edit"),
        "nivel": nivel_de(c.rol_proyecto, c.permiso),
    } for c, nombre in filas]


async def listar_rechazados(db: AsyncSession, proyecto_id: int) -> List[Dict[str, Any]]:
    """Personas a las que el anfitrión rechazó la solicitud de entrar (el rechazo queda guardado)."""
    filas = (await db.execute(
        select(ColaboradorProyecto.usuario_id, Usuario.nombre, Usuario.email)
        .join(Usuario, Usuario.id == ColaboradorProyecto.usuario_id)
        .where(ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.estado == "rechazado")
        .order_by(Usuario.nombre)
    )).all()
    return [{"usuario_id": uid, "nombre": nombre, "email": email} for uid, nombre, email in filas]


async def permitir_de_nuevo(db: AsyncSession, proyecto_id: int, usuario_id: int) -> Dict[str, Any]:
    """El anfitrión se arrepiente de un rechazo: la persona pasa a ser miembro aprobado
    (con el permiso que tenía guardado, editor por defecto). Le llega el aviso de aprobación."""
    c = (await db.execute(select(ColaboradorProyecto).where(
        ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.usuario_id == usuario_id
    ))).scalar_one_or_none()
    if c is None or c.estado != "rechazado":
        raise HTTPException(status_code=404, detail="Esa persona no tiene una solicitud rechazada en este proyecto.")
    c.estado = "aprobado"
    await db.commit()
    return {"usuario_id": usuario_id, "estado": "aprobado"}


async def cambiar_permiso(db: AsyncSession, proyecto_id: int, usuario_id: int, permiso: str) -> Dict[str, Any]:
    if permiso not in PERMISOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Permiso inválido: usa 'edit' (editor) o 'view' (lector).")
    c = (await db.execute(select(ColaboradorProyecto).where(
        ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.usuario_id == usuario_id
    ))).scalar_one_or_none()
    if c is None or c.estado != "aprobado":
        raise HTTPException(status_code=404, detail="Esa persona no es miembro aprobado del proyecto.")
    if c.rol_proyecto == "anfitrion":
        raise HTTPException(status_code=400, detail="El anfitrión siempre puede editar.")
    c.permiso = permiso
    await db.commit()
    await aplicar_en_sala(db, proyecto_id, usuario_id, permiso)
    return {"usuario_id": usuario_id, "permiso": permiso, "nivel": nivel_de(c.rol_proyecto, permiso)}


async def aplicar_en_sala(db: AsyncSession, proyecto_id: int, usuario_id: int, permiso: str) -> None:
    """Si la persona está conectada a la sala, el cambio se aplica al momento (sin recargar)."""
    from backend.core.websockets.connection_manager import manager

    codigo = (await db.execute(select(Proyecto.codigo_acceso).where(Proyecto.id == proyecto_id))).scalar()
    sala = manager.salas.get(codigo or "")
    if not sala:
        return
    gid = f"auth_{usuario_id}"
    if permiso == "view":
        sala["readonly_guests"].add(gid)
    else:
        sala["readonly_guests"].discard(gid)
    rol = "view" if permiso == "view" else "edit"
    if gid in sala["guests"]:
        await manager.send_personal_message({"type": "role_changed", "role": rol}, sala["guests"][gid])
    if sala.get("host") is not None:
        await manager.send_personal_message({"type": "role_updated", "guest_id": gid, "role": rol}, sala["host"])


async def permiso_guardado(db, codigo_acceso: str, guest_id: str) -> Optional[Dict[str, str]]:
    """Para el WebSocket: estado y permiso guardados de un invitado con cuenta (guest_id 'auth_<id>')."""
    if not str(guest_id).startswith("auth_") or not str(guest_id)[5:].isdigit():
        return None
    fila = (await db.execute(
        select(ColaboradorProyecto.estado, ColaboradorProyecto.permiso, ColaboradorProyecto.rol_proyecto)
        .join(Proyecto, Proyecto.id == ColaboradorProyecto.proyecto_id)
        .where(Proyecto.codigo_acceso == codigo_acceso, ColaboradorProyecto.usuario_id == int(str(guest_id)[5:]))
    )).first()
    if not fila:
        return None
    return {"estado": fila.estado, "permiso": fila.permiso or "edit", "rol_proyecto": fila.rol_proyecto}


async def guardar_desde_sala(db, codigo_acceso: str, guest_id: str, rol: str) -> bool:
    """El anfitrión cambió el rol en la sala (WebSocket): se guarda para la próxima vez."""
    if not str(guest_id).startswith("auth_") or not str(guest_id)[5:].isdigit():
        return False
    c = (await db.execute(
        select(ColaboradorProyecto)
        .join(Proyecto, Proyecto.id == ColaboradorProyecto.proyecto_id)
        .where(Proyecto.codigo_acceso == codigo_acceso, ColaboradorProyecto.usuario_id == int(str(guest_id)[5:]))
    )).scalar_one_or_none()
    if c is None or c.rol_proyecto == "anfitrion":
        return False
    c.permiso = "view" if rol == "view" else "edit"
    await db.commit()
    return True
