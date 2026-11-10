"""
Presencia en la sala y menciones del chat.

- Presencia: cada vez que alguien entra o sale (web o app móvil) el servidor envía a TODA la sala
  `{"type": "presence", "users": [...]}` con quién está conectado ahora. Antes el contador
  "en línea" del chat se armaba con los cursores del lienzo, así que quien miraba desde el móvil
  (que no mueve el mouse) nunca contaba.
- Menciones: si un mensaje del chat dice `@Nombre` (o `@todos`), los miembros mencionados reciben
  una notificación (campana + push de Firebase), estén o no conectados.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional

from backend.core.websockets.connection_manager import manager

_MENCIONES_TODOS = {"todos", "all", "everyone", "sala"}


def _norm(texto: Optional[str]) -> str:
    return unicodedata.normalize("NFKD", (texto or "").strip()).encode("ascii", "ignore").decode().lower()


def usuarios_en_linea(codigo_acceso: str) -> List[Dict[str, Any]]:
    """Conectados ahora mismo: el anfitrión y los invitados ya admitidos (no los que esperan)."""
    sala = manager.salas.get(codigo_acceso)
    if not sala:
        return []
    apodos = sala.get("guest_nicknames", {})
    usuarios: List[Dict[str, Any]] = []
    if sala.get("host") is not None:
        hid = sala.get("host_id") or "host"
        usuarios.append({"id": hid, "nickname": apodos.get(hid) or "Anfitrión", "role": "host",
                         "device": "web"})
    for gid in list(sala.get("guests", {})):
        if gid in sala.get("pending_guests", {}) or gid not in sala.get("approved_guests", set()):
            continue
        usuarios.append({
            "id": gid,
            "nickname": apodos.get(gid) or "Invitado",
            "role": "view" if gid in sala.get("readonly_guests", set()) else "edit",
            "device": "movil" if str(gid).startswith("mob_") else "web",
        })
    return usuarios


async def anunciar_presencia(codigo_acceso: str) -> None:
    if codigo_acceso in manager.salas:
        await manager.broadcast_to_sala({"type": "presence", "users": usuarios_en_linea(codigo_acceso)},
                                        codigo_acceso)


# ─── Menciones ──────────────────────────────────────────────────────────────

def mencionados(texto: str, miembros: List[Dict[str, Any]], autor: str = "") -> List[int]:
    """
    ids de los miembros que el texto menciona con @. Acepta el nombre completo (`@Ana Pérez`),
    solo el primer nombre (`@ana`) y sin tildes; `@todos` menciona a todos menos al autor.
    """
    t = _norm(texto)
    if "@" not in t:
        return []
    autor_n = _norm(autor)
    etiquetas = set(re.findall(r"@([a-z0-9_.\-]+)", t))
    todos = bool(etiquetas & _MENCIONES_TODOS)
    ids: List[int] = []
    for m in miembros:
        nombre = _norm(m.get("nombre"))
        if not nombre or nombre == autor_n:
            continue
        partes = nombre.split()
        juntos = re.sub(r"\s+", "", nombre)
        if (todos or f"@{nombre}" in t or juntos in etiquetas
                or (partes and partes[0] in etiquetas)):
            ids.append(m["id"])
    return list(dict.fromkeys(ids))


async def procesar_mencion(codigo_acceso: str, chat_msg: Any) -> None:
    """Encola la notificación 'mencion' (una vez por mensaje; las respuestas de la IA no cuentan)."""
    if not isinstance(chat_msg, dict) or chat_msg.get("isAi"):
        return
    texto = str(chat_msg.get("text") or "")
    if "@" not in texto:
        return
    sala = manager.salas.get(codigo_acceso)
    msg_id = chat_msg.get("id")
    if sala is not None and msg_id:
        vistos = sala.setdefault("menciones_avisadas", set())
        if msg_id in vistos:   # el mismo mensaje se reenvía al actualizarse (p. ej. estado de la IA)
            return
        vistos.add(msg_id)
        if len(vistos) > 1000:
            vistos.clear()

    from sqlalchemy import select
    from backend.core.database import AsyncSessionLocal
    from backend.modules.gestion_proyectos.models import Proyecto
    from backend.modules.gestion_notificaciones.services import notificaciones_service as notif

    async with AsyncSessionLocal() as db:
        proyecto_id = (await db.execute(
            select(Proyecto.id).where(Proyecto.codigo_acceso == codigo_acceso)
        )).scalar_one_or_none()
    if proyecto_id is None:
        return
    notif.programar([{
        "tipo": "mencion",
        "proyecto_id": proyecto_id,
        "autor": chat_msg.get("senderName") or "Alguien",
        "autor_guest": chat_msg.get("senderId"),
        "texto": texto,
    }])
