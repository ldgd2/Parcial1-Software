from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.modules.gestion_asistencia_ia.notificaciones.schemas.request import NotificationRequest
from backend.modules.gestion_asistencia_ia.notificaciones.schemas.response import NotificationResponse
from backend.modules.gestion_asistencia_ia.notificaciones.services.notifications_service import NotificationsService

router = APIRouter(prefix="/api/notifications", tags=["Notificaciones"])

@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    payload: NotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Only the authenticated user can send a notification for themselves
    if payload.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para enviar notificaciones a este usuario",
        )
    message_id = await NotificationsService.send_notification(
        db=db,
        user_id=payload.user_id,
        title=payload.title,
        body=payload.body,
        data=payload.data,
    )
    return NotificationResponse(message_id=message_id)

