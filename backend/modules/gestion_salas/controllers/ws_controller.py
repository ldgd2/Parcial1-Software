from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.core.websockets.connection_manager import manager
from backend.core.database import get_db
from backend.modules.gestion_proyectos.versioning.models import GitObject, Commit
from sqlalchemy import select
import json

router = APIRouter(tags=["WebSockets Salas"])


async def _save_delta_to_db(new_objects: dict, head_hash: str, author: str):
    """Guarda los nuevos GitObjects y el Commit en PostgreSQL."""
    async for db in get_db():
        for obj_hash, obj_data in new_objects.items():
            exists = await db.execute(select(GitObject).where(GitObject.hash == obj_hash))
            if not exists.scalar_one_or_none():
                db.add(GitObject(
                    hash=obj_hash,
                    type=obj_data.get("type"),
                    content=obj_data.get("data"),
                ))

        commit_exists = await db.execute(select(Commit).where(Commit.hash == head_hash))
        if not commit_exists.scalar_one_or_none():
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


async def _get_snapshots(codigo_acceso: str) -> list:
    """
    Devuelve la snapshot de versiones de todas las clases del proyecto.
    Lee el lienzo_json del Proyecto para asegurar aislamiento entre proyectos.
    """
    from backend.modules.gestion_proyectos.models import Proyecto
    import json
    
    snapshots = []
    async for db in get_db():
        result = await db.execute(
            select(Proyecto).where(Proyecto.codigo_acceso == codigo_acceso)
        )
        proyecto = result.scalar_one_or_none()

        if proyecto and proyecto.lienzo_json:
            try:
                lienzo = json.loads(proyecto.lienzo_json) if isinstance(proyecto.lienzo_json, str) else proyecto.lienzo_json
                nodes = lienzo.get("nodes", [])
                for node in nodes:
                    snapshots.append({
                        "nodeId": node.get("id"),
                        "version": node.get("version", 0),
                        "hash": node.get("hash", ""),
                        "atributos": node.get("atributos", []),
                        "metodos": node.get("metodos", []),
                    })
            except Exception:
                pass
        break

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
        await manager.connect_host(websocket, codigo_acceso)

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
                            manager.remove_pending_guest(codigo_acceso, target_guest)
                            manager.salas[codigo_acceso]["approved_guests"].add(target_guest)
                            await manager.broadcast_to_sala(
                                {"type": "user_joined", "nickname": manager.salas[codigo_acceso]["pending_guests"].get(target_guest, "Guest")},
                                codigo_acceso,
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
                                if approved:
                                    solicitud.estado = "aprobado"
                                else:
                                    await db.delete(solicitud)
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
                    if new_role == "view":
                        sala["readonly_guests"].add(target_guest)
                    else:
                        sala["readonly_guests"].discard(target_guest)
                    
                    if target_guest in sala["guests"]:
                        await manager.send_personal_message({"type": "role_changed", "role": new_role}, sala["guests"][target_guest])
                    await manager.send_personal_message({"type": "role_updated", "guest_id": target_guest, "role": new_role}, websocket)

                elif msg_type == "request_snapshots":
                    snapshots = await _get_snapshots(codigo_acceso)
                    await manager.send_personal_message(
                        {"type": "snapshots_response", "snapshots": snapshots},
                        websocket,
                    )

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
                    await manager.broadcast_to_sala(message, codigo_acceso, exclude=websocket)

        except WebSocketDisconnect:
            manager.disconnect(websocket, codigo_acceso)

    else:  # Guest
        if not guest_id or not nickname:
            await websocket.close(code=1008)
            return

        await manager.connect_guest(websocket, codigo_acceso, guest_id)

        if guest_id in manager.salas[codigo_acceso]["approved_guests"]:
            await manager.send_personal_message({"type": "admission_status", "approved": True}, websocket)
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

                # ── Delta del guest: guardar en BD y propagar ─────────────
                elif msg_type in ("sync_offline", "diagram_delta"):
                    if guest_id in manager.salas[codigo_acceso]["readonly_guests"]:
                        continue # Solo lectura
                        
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
                    if guest_id in manager.salas[codigo_acceso]["readonly_guests"] and msg_type == "diagram_event":
                        continue
                    await manager.broadcast_to_sala(message, codigo_acceso, exclude=websocket)

        except WebSocketDisconnect:
            manager.disconnect(websocket, codigo_acceso)
            manager.remove_pending_guest(codigo_acceso, guest_id)
            await manager.notify_host(codigo_acceso, {
                "type": "guest_left",
                "guest_id": guest_id,
            })
