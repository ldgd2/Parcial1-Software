import json
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from backend.modules.gestion_asistencia_ia.notificaciones.models import NotificationToken, NotificationLog
from backend.modules.gestion_asistencia_ia.notificaciones.firebase_init import send_fcm_message

class NotificationsService:
    @staticmethod
    async def _get_device_token(db: AsyncSession, user_id: int) -> Optional[str]:
        result = await db.execute(select(NotificationToken.device_token).where(NotificationToken.user_id == user_id))
        token_row = result.scalar_one_or_none()
        return token_row

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
        from backend.modules.gestion_asistencia_ia.notificaciones.repositories.preference_repository import PreferenceRepository
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

        token = await NotificationsService._get_device_token(db, user_id)
        if not token:
            raise ValueError("Device token not found for user")
        # Send via Firebase (synchronous call)
        message_id = send_fcm_message(token, title, body, data)
        # Retrieve token record id for log
        result = await db.execute(select(NotificationToken.id).where(NotificationToken.user_id == user_id))
        token_id = result.scalar_one()
        await NotificationsService._log_notification(db, token_id, title, body, data)
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

