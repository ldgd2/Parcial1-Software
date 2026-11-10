from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt
from backend.core.config import settings
from backend.core.websockets.connection_manager import manager
from backend.core.database import get_db
from backend.modules.gestion_proyectos.versioning.models import GitObject, Commit
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
from sqlalchemy import select
import asyncio
import json

router = APIRouter(tags=["WebSockets Salas"])


async def _usuario_del_token(token: str | None) -> int | None:
    """id del usuario de un JWT válido y no revocado; None si no lo es."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        usuario_id = int(payload.get("sub"))
    except Exception:
        return None
    from backend.modules.gestion_usuarios.dependencies import _revocado
    async for db in get_db():
        if await _revocado(db, token):
            return None
        break
    return usuario_id


async def _leer_token_inicial(websocket: WebSocket) -> str | None:
    """El token llega en el PRIMER mensaje ({type: 'auth'}), no en la URL."""
    try:
        primero = json.loads(await asyncio.wait_for(websocket.receive_text(), timeout=5))
        if isinstance(primero, dict) and primero.get("type") == "auth":
            return primero.get("token")
    except (asyncio.TimeoutError, ValueError, WebSocketDisconnect):
        pass
    return None


async def _usuario_anfitrion(codigo_acceso: str, token: str | None) -> int | None:
    """
    Devuelve el id del usuario si el token es válido y pertenece a un ANFITRIÓN
    aprobado del proyecto con ese código de acceso; si no, None.

    Antes el rol de host se tomaba del parámetro `user_type` de la URL, sin
    verificar nada: cualquiera con el código de sala podía entrar como host
    (aprobar invitados, expulsar, cambiar roles).
    """
    usuario_id = await _usuario_del_token(token)
    if usuario_id is None:
        return None

    async for db in get_db():
        resultado = await db.execute(
            select(ColaboradorProyecto.usuario_id)
            .join(Proyecto, Proyecto.id == ColaboradorProyecto.proyecto_id)
            .where(
                Proyecto.codigo_acceso == codigo_acceso,
                ColaboradorProyecto.usuario_id == usuario_id,
                ColaboradorProyecto.rol_proyecto == "anfitrion",
                ColaboradorProyecto.estado == "aprobado",
            )
        )
        return usuario_id if resultado.scalar_one_or_none() is not None else None
    return None


def _usuario_de_guest(guest_id: str | None) -> int | None:
    """'auth_15' -> 15 (colaborador registrado); invitados anónimos -> None."""
    if guest_id and str(guest_id).startswith("auth_"):
        try:
            return int(str(guest_id).split("_", 1)[1])
        except ValueError:
            return None
    return None


async def _proyecto_de_sala(db, codigo_acceso: str) -> int | None:
    resultado = await db.execute(select(Proyecto.id).where(Proyecto.codigo_acceso == codigo_acceso))
    return resultado.scalar_one_or_none()


async def _guardar_rol(codigo_acceso: str, guest_id: str, lector: bool) -> None:
    """CU38: el rol elegido en Permisos de Acceso se guarda en colaboradores_proyecto
    (antes vivía solo en memoria del WebSocket y se perdía al recargar o reiniciar)."""
    usuario_id = _usuario_de_guest(guest_id)
    if usuario_id is None:
        return
    from backend.core.permissions.proyecto import guardar_permiso
    async for db in get_db():
        proyecto_id = await _proyecto_de_sala(db, codigo_acceso)
        if proyecto_id:
            await guardar_permiso(db, proyecto_id, usuario_id, lector)
        break


async def aplicar_rol_en_vivo(codigo_acceso: str, usuario_id: int, lector: bool) -> None:
    """Refleja en la sala un cambio de permiso hecho por REST (invitar / cambiar permiso)."""
    sala = manager.salas.get(codigo_acceso)
    if sala is None:
        return
    guest_id = f"auth_{usuario_id}"
    rol = "view" if lector else "edit"
    if lector:
        sala["readonly_guests"].add(guest_id)
    else:
        sala["readonly_guests"].discard(guest_id)
    if guest_id in sala["guests"]:
        await manager.send_personal_message({"type": "role_changed", "role": rol}, sala["guests"][guest_id])
    if sala.get("host") is not None:
        await manager.send_personal_message({"type": "role_updated", "guest_id": guest_id, "role": rol}, sala["host"])


async def _estado_guardado(codigo_acceso: str, guest_id: str) -> tuple[bool, bool]:
    """(aprobado, lector) del colaborador registrado según colaboradores_proyecto."""
    usuario_id = _usuario_de_guest(guest_id)
    if usuario_id is None:
        return False, False
    from backend.core.permissions.proyecto import obtener_colaborador, es_lector
    async for db in get_db():
        proyecto_id = await _proyecto_de_sala(db, codigo_acceso)
        if not proyecto_id:
            return False, False
        colaborador = await obtener_colaborador(db, proyecto_id, usuario_id)
        return bool(colaborador and colaborador.estado == "aprobado"), es_lector(colaborador)
    return False, False


async def _save_delta_to_db(new_objects: dict, head_hash: str, author: str):
    """Guarda los nuevos GitObjects y el Commit en PostgreSQL usando inserciones masivas."""
    async for db in get_db():
        hashes = list(new_objects.keys())
        if hashes:
            # Buscar hashes existentes en una sola consulta
            existing_result = await db.execute(select(GitObject.hash).where(GitObject.hash.in_(hashes)))
            existing_hashes = set(existing_result.scalars().all())

            # Preparar los nuevos objetos a insertar
            objs_to_add = []
            for obj_hash, obj_data in new_objects.items():
                if obj_hash not in existing_hashes:
                    objs_to_add.append(GitObject(
                        hash=obj_hash,
                        type=obj_data.get("type"),
                        content=obj_data.get("data"),
                    ))
            
            if objs_to_add:
                db.add_all(objs_to_add)

        # Manejar el commit
        if head_hash:
            commit_exists = await db.execute(select(Commit).where(Commit.hash == head_hash))
            if not commit_exists.scalar_one_or_none():
                # Ensure the tree object exists
                tree_exists = await db.execute(select(GitObject.hash).where(GitObject.hash == head_hash))
                if not tree_exists.scalar_one_or_none():
                    db.add(GitObject(hash=head_hash, type="tree", content={"source": "sync_offline"}))
                    
                # Obtener el commit anterior más reciente para encadenarlo
                last_commit = await db.execute(
                    select(Commit).order_by(Commit.created_at.desc()).limit(1)
                )
                last = last_commit.scalar_one_or_none()
                db.add(Commit(
                    hash=head_hash,
                    tree_hash=head_hash,
                    parent_hash=last.hash if last else None,
                    author=author,
                    message="Diagram update via WebSocket",
                ))

        await db.commit()
        break  # Solo una sesión


async def _estado_vivo(codigo_acceso: str) -> dict:
    """
    Estado vivo de las clases de la sala: el lienzo guardado más los diagram_event recibidos
    desde entonces. Quien vuelve de estar sin conexión compara contra esto, así ve también los
    cambios que los demás aún no guardaron (el autoguardado es cada 30 s) y se detectan los
    conflictos (CP23). Se reinicia con el lienzo cada vez que alguien guarda.
    """
    sala = manager.salas.get(codigo_acceso)
    if sala is not None and sala.get("estado_vivo") is not None:
        return sala["estado_vivo"]

    nodos = {}
    async for db in get_db():
        result = await db.execute(select(Proyecto).where(Proyecto.codigo_acceso == codigo_acceso))
        proyecto = result.scalar_one_or_none()
        if proyecto and proyecto.lienzo_json:
            try:
                lienzo = json.loads(proyecto.lienzo_json) if isinstance(proyecto.lienzo_json, str) else proyecto.lienzo_json
                nodos = {n.get("id"): dict(n) for n in lienzo.get("nodes", []) if isinstance(n, dict) and n.get("id")}
            except Exception:
                nodos = {}
        break
    if sala is not None:
        sala["estado_vivo"] = nodos
    return nodos


def _aplicar_en_lista(items: list, item_id, partial: dict | None, borrar: bool = False) -> list:
    if borrar:
        return [i for i in items if i.get("id") != item_id]
    return [{**i, **(partial or {})} if i.get("id") == item_id else i for i in items]


async def _aplicar_evento_vivo(codigo_acceso: str, mensaje: dict) -> None:
    """Refleja un diagram_event (el mismo que se reenvía a la sala) en el estado vivo."""
    evento = mensaje.get("payload") or {}
    accion, p = evento.get("action"), evento.get("payload") or {}
    if not accion:
        return
    nodos = await _estado_vivo(codigo_acceso)
    try:
        if accion == "addNode" and isinstance(p.get("node"), dict):
            nodos[p["node"].get("id")] = dict(p["node"])
        elif accion == "updateNode" and p.get("id") in nodos:
            nodos[p["id"]].update(p.get("partial") or {})
            nodos[p["id"]]["version"] = int(nodos[p["id"]].get("version") or 0) + 1
        elif accion == "moveNode" and p.get("id") in nodos:
            nodos[p["id"]].update({"x": p.get("x"), "y": p.get("y")})
        elif accion == "deleteNode":
            nodos.pop(p.get("id"), None)
        elif accion in ("addAtributo", "updateAtributo", "deleteAtributo", "addMetodo", "updateMetodo", "deleteMetodo"):
            nodo = nodos.get(p.get("nodeId"))
            if nodo is None:
                return
            campo = "atributos" if "Atributo" in accion else "metodos"
            lista = list(nodo.get(campo) or [])
            if accion.startswith("add"):
                lista.append(p.get("attr") if campo == "atributos" else p.get("met"))
            else:
                item_id = p.get("attrId") if campo == "atributos" else p.get("metodId")
                lista = _aplicar_en_lista(lista, item_id, p.get("partial"), borrar=accion.startswith("delete"))
            nodo[campo] = [i for i in lista if isinstance(i, dict)]
            nodo["version"] = int(nodo.get("version") or 0) + 1
    except Exception:
        # Un evento con forma inesperada no debe cortar la sala; el estado se rehace al guardar
        sala = manager.salas.get(codigo_acceso)
        if sala is not None:
            sala["estado_vivo"] = None


def reiniciar_estado_vivo(codigo_acceso: str, lienzo: dict | None) -> None:
    """Al guardar el lienzo, el estado vivo pasa a ser exactamente lo guardado."""
    sala = manager.salas.get(codigo_acceso)
    if sala is None:
        return
    if not isinstance(lienzo, dict):
        sala["estado_vivo"] = None  # se vuelve a leer de la BD en la próxima consulta
        return
    sala["estado_vivo"] = {n.get("id"): dict(n) for n in lienzo.get("nodes", []) if isinstance(n, dict) and n.get("id")}


async def _get_snapshots(codigo_acceso: str) -> list:
    """Snapshot de cada clase de la sala (estado vivo), con su nombre para detectar conflictos."""
    snapshots = []
    for node in (await _estado_vivo(codigo_acceso)).values():
        snapshots.append({
            "nodeId": node.get("id"),
            "version": node.get("version", 0),
            "hash": node.get("hash", ""),
            "nombre": node.get("nombre"),
            "type": node.get("type"),
            "x": node.get("x"),
            "y": node.get("y"),
            "width": node.get("width"),
            "color": node.get("color"),
            "atributos": node.get("atributos", []),
            "metodos": node.get("metodos", []),
        })
    return snapshots


@router.websocket("/ws/salas/{codigo_acceso}")
async def websocket_endpoint(
    websocket: WebSocket,
    codigo_acceso: str,
    user_type: str = "guest",
    guest_id: str = None,
    nickname: str = None,
):
    if user_type == "host":
        # El rol de host se verifica en el servidor. El token llega en el PRIMER
        # mensaje (no en la URL, que queda en logs de servidores y proxies).
        await websocket.accept()
        token = await _leer_token_inicial(websocket)
        if await _usuario_anfitrion(codigo_acceso, token) is None:
            try:
                await websocket.close(code=1008, reason="No autorizado como anfitrión de esta sala")
            except RuntimeError:
                pass  # el cliente ya cerró
            return
        await manager.connect_host(websocket, codigo_acceso, host_id=guest_id, nickname=nickname, accept=False)

        # Enviar guests pendientes al host
        pending = manager.salas[codigo_acceso].get("pending_guests", {})
        for g_id, g_nick in pending.items():
            await manager.send_personal_message({
                "type": "join_request",
                "guest_id": g_id,
                "nickname": g_nick,
            }, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")

                # ── Admisión de guests ────────────────────────────────────
                if msg_type == "admission_response":
                    target_guest = message.get("guest_id")
                    approved = message.get("approved", False)

                    if target_guest in manager.salas[codigo_acceso]["guests"]:
                        guest_ws = manager.salas[codigo_acceso]["guests"][target_guest]
                        proyecto_id = message.get("proyecto_id")
                        await manager.send_personal_message(
                            {"type": "admission_status", "approved": approved, "proyecto_id": proyecto_id},
                            guest_ws,
                        )
                        if approved:
                            # El apodo se toma ANTES de sacarlo de pendientes (antes siempre salía "Guest")
                            apodo_unido = (manager.salas[codigo_acceso]["pending_guests"].get(target_guest)
                                           or manager.salas[codigo_acceso]["guest_nicknames"].get(target_guest, "Invitado"))
                            manager.remove_pending_guest(codigo_acceso, target_guest)
                            manager.salas[codigo_acceso]["approved_guests"].add(target_guest)
                            if target_guest in manager.salas[codigo_acceso]["readonly_guests"]:
                                await manager.send_personal_message({"type": "role_changed", "role": "view"}, guest_ws)
                            await manager.broadcast_to_sala(
                                {"type": "user_joined", "guest_id": target_guest, "nickname": apodo_unido},
                                codigo_acceso,
                                exclude=guest_ws,
                            )
                        else:
                            await guest_ws.close()

                    elif str(target_guest).startswith("auth_"):
                        proyecto_id = message.get("proyecto_id")
                        user_id = int(target_guest.split("_")[1])
                        async for db in get_db():
                            from backend.modules.gestion_proyectos.administrar_proyecto.repositories.admin_repo import admin_repo
                            solicitud = await admin_repo.get_colaborador(db, proyecto_id, user_id)
                            if solicitud and solicitud.estado == "pendiente":
                                # Rechazo guardado (no se borra la fila: si no, la espera del
                                # invitado volvía a crear la solicitud a los 3 segundos)
                                solicitud.estado = "aprobado" if approved else "rechazado"
                                await db.commit()
                            break
                        if approved:
                            manager.remove_pending_guest(codigo_acceso, target_guest)
                            manager.salas[codigo_acceso]["approved_guests"].add(target_guest)

                # ── Cliente pide snapshots para sincronizar al reconectarse ──
                elif msg_type == "get_room_users":
                    sala = manager.salas[codigo_acceso]
                    users = []
                    for gid in sala["approved_guests"]:
                        nick = sala["guest_nicknames"].get(gid, "Guest")
                        users.append({
                            "id": gid,
                            "nickname": nick,
                            "isOnline": gid in sala["guests"],
                            "role": "view" if gid in sala["readonly_guests"] else "edit"
                        })
                    await manager.send_personal_message({"type": "room_users_list", "users": users}, websocket)

                elif msg_type == "kick_user":
                    target_guest = message.get("guest_id")
                    await manager.kick_user(codigo_acceso, target_guest)
                    await manager.send_personal_message({"type": "user_kicked", "guest_id": target_guest}, websocket)

                elif msg_type == "change_role":
                    target_guest = message.get("guest_id")
                    new_role = message.get("role")
                    sala = manager.salas[codigo_acceso]
                    # CU38: el permiso se GUARDA (antes vivía solo en memoria y se perdía al reconectar)
                    async for db in get_db():
                        from backend.modules.gestion_proyectos.permisos_proyecto.permisos_service import guardar_desde_sala
                        await guardar_desde_sala(db, codigo_acceso, target_guest, new_role)
                        break
                    if new_role == "view":
                        sala["readonly_guests"].add(target_guest)
                    else:
                        sala["readonly_guests"].discard(target_guest)
                    await _guardar_rol(codigo_acceso, target_guest, new_role == "view")

                    if target_guest in sala["guests"]:
                        await manager.send_personal_message({"type": "role_changed", "role": new_role}, sala["guests"][target_guest])
                    await manager.send_personal_message({"type": "role_updated", "guest_id": target_guest, "role": new_role}, websocket)

                elif msg_type == "request_snapshots":
                    snapshots = await _get_snapshots(codigo_acceso)
                    await manager.send_personal_message(
                        {"type": "snapshots_response", "snapshots": snapshots},
                        websocket,
                    )

                # ── Locks ─────────────────────────────────────────────────────────
                elif msg_type == "lock_element":
                    from backend.modules.gestion_concurrencia.bloquear_elemento.services.lock_service import lock_service
                    element_id = message.get("element_id")
                    host_nick = nickname or "Anfitrión"
                    host_user_id = guest_id or "host"
                    if element_id and lock_service.lock_element(codigo_acceso, element_id, host_user_id, host_nick):
                        await manager.broadcast_to_sala(
                            {"type": "element_locked", "element_id": element_id, "nickname": host_nick},
                            codigo_acceso,
                            exclude=websocket
                        )
                    # Broadcast unlocks for any stale keys
                    stale = lock_service.get_stale_locks(codigo_acceso)
                    for st in stale:
                        lock_service.unlock_element(codigo_acceso, st, lock_service.get_locked_elements(codigo_acceso).get(st, {}).get("user_id"))
                        await manager.broadcast_to_sala({"type": "element_unlocked", "element_id": st}, codigo_acceso, exclude=websocket)

                elif msg_type == "refresh_lock":
                    from backend.modules.gestion_concurrencia.bloquear_elemento.services.lock_service import lock_service
                    element_id = message.get("element_id")
                    # Mismo id con el que se tomó el bloqueo (guest_id del anfitrión). Antes se usaba
                    # "host" y no coincidía: el anfitrión nunca liberaba su candado (CP17).
                    if element_id:
                        lock_service.refresh_lock(codigo_acceso, element_id, guest_id or "host")

                elif msg_type == "unlock_element":
                    from backend.modules.gestion_concurrencia.bloquear_elemento.services.lock_service import lock_service
                    element_id = message.get("element_id")
                    if element_id and lock_service.unlock_element(codigo_acceso, element_id, guest_id or "host"):
                        await manager.broadcast_to_sala(
                            {"type": "element_unlocked", "element_id": element_id},
                            codigo_acceso,
                            exclude=websocket
                        )

                # ── Chat grupal tipo WhatsApp ─────────────────────────────
                elif msg_type == "chat_message":
                    chat_msg = message.get("message")
                    if chat_msg and codigo_acceso in manager.salas:
                        history = manager.salas[codigo_acceso].setdefault("chat_history", [])
                        msg_id = chat_msg.get("id")
                        updated = False
                        if msg_id:
                            for idx, existing in enumerate(history):
                                if existing.get("id") == msg_id:
                                    history[idx] = chat_msg
                                    updated = True
                                    break
                        if not updated:
                            history.append(chat_msg)
                        if len(history) > 200:
                            history.pop(0)
                    await manager.broadcast_to_sala(message, codigo_acceso, exclude=websocket)

                elif msg_type == "request_chat_history":
                    history = manager.salas.get(codigo_acceso, {}).get("chat_history", [])
                    await manager.send_personal_message({"type": "chat_history", "messages": history}, websocket)

                # ── Delta del diagrama: guardar en BD y propagar ──────────
                elif msg_type in ("sync_offline", "diagram_delta"):
                    new_objects = message.get("objects", {})
                    head_hash = message.get("head")

                    if new_objects and head_hash:
                        await _save_delta_to_db(new_objects, head_hash, author="host")

                    await manager.broadcast_to_sala(
                        {"type": "diagram_delta", "objects": new_objects, "head": head_hash},
                        codigo_acceso,
                        exclude=websocket,
                    )

                # ── Resto (mouse, etc.) ───────────────────────────────────
                else:
                    if msg_type == "diagram_event":
                        await _aplicar_evento_vivo(codigo_acceso, message)
                    await manager.broadcast_to_sala(message, codigo_acceso, exclude=websocket)

        except WebSocketDisconnect:
            manager.disconnect(websocket, codigo_acceso)

    else:  # Guest
        if not guest_id or not nickname:
            await websocket.close(code=1008)
            return

        # Un invitado "auth_<id>" dice ser un usuario registrado: debe probarlo con su token
        # (antes bastaba con poner auth_<id> en la URL para heredar el permiso de otro usuario).
        await websocket.accept()
        if str(guest_id).startswith("auth_"):
            usuario_token = await _usuario_del_token(await _leer_token_inicial(websocket))
            if usuario_token is None or usuario_token != _usuario_de_guest(guest_id):
                try:
                    await websocket.close(code=1008, reason="Identidad del colaborador no verificada")
                except RuntimeError:
                    pass
                return

        # Con el nickname: sin él, "Permisos de Acceso" mostraba a todos como "Guest"
        await manager.connect_guest(websocket, codigo_acceso, guest_id, nickname=nickname, accept=False)

        # Colaborador registrado ya aprobado en BD: entra sin pasar otra vez por la sala de
        # espera, y con el rol guardado (un lector sigue siéndolo tras recargar o reconectarse).
        aprobado_bd, lector_bd = await _estado_guardado(codigo_acceso, guest_id)
        if aprobado_bd:
            manager.salas[codigo_acceso]["approved_guests"].add(guest_id)
        if lector_bd:
            manager.salas[codigo_acceso]["readonly_guests"].add(guest_id)

        # CU38: un miembro ya aprobado en la base entra directo con su permiso guardado
        guardado = None
        async for db in get_db():
            from backend.modules.gestion_proyectos.permisos_proyecto.permisos_service import permiso_guardado
            guardado = await permiso_guardado(db, codigo_acceso, guest_id)
            break
        sala_actual = manager.salas[codigo_acceso]

        if guardado and guardado["estado"] == "aprobado":
            sala_actual["approved_guests"].add(guest_id)
            solo_lectura = guardado["permiso"] == "view" and guardado["rol_proyecto"] != "anfitrion"
            if solo_lectura:
                sala_actual["readonly_guests"].add(guest_id)
            else:
                sala_actual["readonly_guests"].discard(guest_id)
            await manager.send_personal_message({"type": "admission_status", "approved": True}, websocket)
            await manager.send_personal_message({"type": "role_changed", "role": "view" if solo_lectura else "edit"}, websocket)
        elif (
            user_type in ("viewer", "observer")
            or str(guest_id).startswith("mob_")
            or str(guest_id).startswith("viewer_")
        ):
            manager.salas[codigo_acceso]["approved_guests"].add(guest_id)
            # Solo los visores/móviles entran en solo lectura por defecto. Antes TODO invitado ya
            # aprobado que se reconectaba quedaba como lector, aunque el anfitrión lo hubiera hecho editor.
            if user_type in ("viewer", "observer") or str(guest_id).startswith(("mob_", "viewer_")):
                manager.salas[codigo_acceso]["readonly_guests"].add(guest_id)
            await manager.send_personal_message({"type": "admission_status", "approved": True}, websocket)
            # CU13: los demás participantes se enteran de que entró
            await manager.broadcast_to_sala(
                {"type": "user_joined", "guest_id": guest_id, "nickname": nickname or "Invitado"},
                codigo_acceso,
                exclude=websocket,
            )
            if guest_id in manager.salas[codigo_acceso]["readonly_guests"]:
            # Visores (app móvil, enlaces de solo ver): siempre solo lectura
            sala_actual["approved_guests"].add(guest_id)
            sala_actual["readonly_guests"].add(guest_id)
            await manager.send_personal_message({"type": "admission_status", "approved": True}, websocket)
        elif guest_id in sala_actual["approved_guests"]:
            # Reconexión de un invitado ya admitido: conserva el rol que tenía
            # (antes se le forzaba solo lectura al reconectarse)
            await manager.send_personal_message({"type": "admission_status", "approved": True}, websocket)
            if guest_id in sala_actual["readonly_guests"]:
                await manager.send_personal_message({"type": "role_changed", "role": "view"}, websocket)
        else:
            manager.add_pending_guest(codigo_acceso, guest_id, nickname)
            await manager.notify_host(codigo_acceso, {
                "type": "join_request",
                "guest_id": guest_id,
                "nickname": nickname,
            })

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")

                # ── Guest pide snapshots ──────────────────────────────────
                if msg_type == "request_snapshots":
                    snapshots = await _get_snapshots(codigo_acceso)
                    await manager.send_personal_message(
                        {"type": "snapshots_response", "snapshots": snapshots},
                        websocket,
                    )

                # ── Locks ─────────────────────────────────────────────────────────
                elif msg_type == "lock_element":
                    from backend.modules.gestion_concurrencia.bloquear_elemento.services.lock_service import lock_service
                    element_id = message.get("element_id")
                    if element_id and lock_service.lock_element(codigo_acceso, element_id, guest_id, nickname):
                        await manager.broadcast_to_sala(
                            {"type": "element_locked", "element_id": element_id, "nickname": nickname},
                            codigo_acceso,
                            exclude=websocket
                        )
                    # Broadcast unlocks for any stale keys
                    stale = lock_service.get_stale_locks(codigo_acceso)
                    for st in stale:
                        lock_service.unlock_element(codigo_acceso, st, lock_service.get_locked_elements(codigo_acceso).get(st, {}).get("user_id"))
                        await manager.broadcast_to_sala({"type": "element_unlocked", "element_id": st}, codigo_acceso, exclude=websocket)

                elif msg_type == "refresh_lock":
                    from backend.modules.gestion_concurrencia.bloquear_elemento.services.lock_service import lock_service
                    element_id = message.get("element_id")
                    if element_id:
                        lock_service.refresh_lock(codigo_acceso, element_id, guest_id)

                elif msg_type == "unlock_element":
                    from backend.modules.gestion_concurrencia.bloquear_elemento.services.lock_service import lock_service
                    element_id = message.get("element_id")
                    if element_id and lock_service.unlock_element(codigo_acceso, element_id, guest_id):
                        await manager.broadcast_to_sala(
                            {"type": "element_unlocked", "element_id": element_id},
                            codigo_acceso,
                            exclude=websocket
                        )

                # ── Chat grupal tipo WhatsApp ─────────────────────────────
                elif msg_type == "chat_message":
                    chat_msg = message.get("message")
                    if chat_msg and codigo_acceso in manager.salas:
                        history = manager.salas[codigo_acceso].setdefault("chat_history", [])
                        msg_id = chat_msg.get("id")
                        updated = False
                        if msg_id:
                            for idx, existing in enumerate(history):
                                if existing.get("id") == msg_id:
                                    history[idx] = chat_msg
                                    updated = True
                                    break
                        if not updated:
                            history.append(chat_msg)
                        if len(history) > 200:
                            history.pop(0)
                    await manager.broadcast_to_sala(message, codigo_acceso, exclude=websocket)

                elif msg_type == "request_chat_history":
                    history = manager.salas.get(codigo_acceso, {}).get("chat_history", [])
                    await manager.send_personal_message({"type": "chat_history", "messages": history}, websocket)

                # ── Delta del guest: guardar en BD y propagar ─────────────
                elif msg_type in ("sync_offline", "diagram_delta"):
                    sala_actual = manager.salas[codigo_acceso]
                    if guest_id in sala_actual["readonly_guests"] or guest_id not in sala_actual["approved_guests"]:
                        continue # Solo lectura, o invitado aún no admitido por el anfitrión
                        
                    new_objects = message.get("objects", {})
                    head_hash = message.get("head")

                    if new_objects and head_hash:
                        await _save_delta_to_db(new_objects, head_hash, author=guest_id)

                    await manager.broadcast_to_sala(
                        {"type": "diagram_delta", "objects": new_objects, "head": head_hash},
                        codigo_acceso,
                        exclude=websocket,
                    )

                else:
                    sala_actual = manager.salas[codigo_acceso]
                    if msg_type == "diagram_event" and (
                        guest_id in sala_actual["readonly_guests"] or guest_id not in sala_actual["approved_guests"]
                    ):
                        continue
                    if msg_type == "diagram_event":
                        await _aplicar_evento_vivo(codigo_acceso, message)
                    await manager.broadcast_to_sala(message, codigo_acceso, exclude=websocket)

        except WebSocketDisconnect:
            manager.disconnect(websocket, codigo_acceso)
            manager.remove_pending_guest(codigo_acceso, guest_id)
            await manager.notify_host(codigo_acceso, {
                "type": "guest_left",
                "guest_id": guest_id,
            })
