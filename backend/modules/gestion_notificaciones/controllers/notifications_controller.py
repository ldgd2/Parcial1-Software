from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_notificaciones.schemas.request import NotificationRequest
from backend.modules.gestion_notificaciones.schemas.response import NotificationResponse
from backend.modules.gestion_notificaciones.services.notifications_service import NotificationsService, SinDispositivo

router = APIRouter(prefix="/api/notifications", tags=["Notificaciones"])

@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    payload: NotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Only the authenticated user can send a notification for themselves
    if payload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para enviar notificaciones a este usuario",
        )
    try:
        message_id = await NotificationsService.send_notification(
            db=db,
            user_id=payload.user_id,
            title=payload.title,
            body=payload.body,
            data=payload.data,
        )
    except SinDispositivo as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:   # firebase-admin no instalado o sin credenciales
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    if not message_id:
        return NotificationResponse(message_id="", detail="No se envió: las preferencias del usuario lo silencian")
    return NotificationResponse(message_id=message_id)
