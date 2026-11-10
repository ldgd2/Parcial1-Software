import asyncio
import json
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from backend.modules.gestion_notificaciones.models import NotificationToken, NotificationLog
from backend.modules.gestion_notificaciones.firebase_init import send_fcm_message


class SinDispositivo(LookupError):
    """El usuario no registró ningún celular (tabla notifications)."""


class NotificationsService:
    @staticmethod
    async def _get_device_token(db: AsyncSession, user_id: int) -> Optional[str]:
        # Un usuario puede tener varias filas (cambió de celular): se usa la más reciente.
        result = await db.execute(
            select(NotificationToken.device_token)
            .where(NotificationToken.user_id == user_id)
            .order_by(NotificationToken.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _log_notification(db: AsyncSession, token_id: int, title: str, body: str, data: Optional[Dict[str, str]]) -> None:
        log_stmt = insert(NotificationLog).values(
            notification_id=token_id,
            title=title,
            body=body,
            data=json.dumps(data) if data else None,
            sent=True,
        )
        await db.execute(log_stmt)
        await db.commit()

    @staticmethod
    async def _should_send(db: AsyncSession, user_id: int, priority: int) -> bool:
        # Retrieve user preferences
        from backend.modules.gestion_notificaciones.repositories.preference_repository import PreferenceRepository
        prefs = await PreferenceRepository.get_by_user(db, user_id)
        if not prefs:
            # default behavior if no prefs stored
            return priority >= 4
        # Quiet mode overrides low priorities
        if prefs.quiet_mode:
            if prefs.quiet_mode_until and prefs.quiet_mode_until > datetime.utcnow():
                # still in quiet period
                return priority >= 4
            # quiet_mode without until => always on
            return priority >= 4
        # Map preference fields to types
        # For simplicity, allow all high priority notifications
        if priority >= 4:
            return True
        # Low/medium priority filtering based on preferences
        # Assume type mapping handled by caller via data['type']
        return True

    @staticmethod
    async def send_notification(
        db: AsyncSession,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: int = 4,
    ) -> str:
        """Envía un push al último celular registrado del usuario. Devuelve el id de FCM ("" si sus
        preferencias lo silencian). Lanza SinDispositivo si no tiene celular registrado."""
        if not await NotificationsService._should_send(db, user_id, priority):
            return ""
        fila = (await db.execute(
            select(NotificationToken.id, NotificationToken.device_token)
            .where(NotificationToken.user_id == user_id)
            .order_by(NotificationToken.id.desc())
            .limit(1)
        )).first()
        if not fila:
            raise SinDispositivo("El usuario no tiene un celular registrado para notificaciones push")
        # firebase-admin es síncrono: se manda en un hilo para no bloquear el servidor
        message_id = await asyncio.to_thread(send_fcm_message, fila.device_token, title, body, data)
        await NotificationsService._log_notification(db, fila.id, title, body, data)
        return message_id

    # Internal event helpers
    @staticmethod
    async def send_change_notification(db: AsyncSession, user_id: int, change_type: str, details: dict) -> str:
        title = f"Cambio en {change_type}"
        body = json.dumps(details)
        return await NotificationsService.send_notification(db, user_id, title, body)

    @staticmethod
    async def send_task_assigned(db: AsyncSession, user_id: int, task_id: int, project_id: int) -> str:
        title = "Tarea asignada"
        body = f"Se te ha asignado la tarea {task_id} en el proyecto {project_id}."
        return await NotificationsService.send_notification(db, user_id, title, body)

    @staticmethod
    async def send_comment_notification(db: AsyncSession, user_id: int, diagram_id: int, comment_id: int) -> str:
        title = "Nuevo comentario en diagrama"
        body = f"Comentario {comment_id} añadido al diagrama {diagram_id}."
        return await NotificationsService.send_notification(db, user_id, title, body)

    @staticmethod
    async def send_room_invite(db: AsyncSession, user_id: int, room_id: int) -> str:
        title = "Invitación a sala"
        body = f"Has sido invitado a la sala {room_id}."
        return await NotificationsService.send_notification(db, user_id, title, body)

