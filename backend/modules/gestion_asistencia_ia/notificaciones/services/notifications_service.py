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
    async def send_notification(
        db: AsyncSession,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> str:
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

