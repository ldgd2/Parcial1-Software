from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_asistencia_ia.notificaciones.schemas.token_request import TokenRegisterRequest
from backend.modules.gestion_asistencia_ia.notificaciones.models import NotificationToken
from sqlalchemy import select, insert, update

router = APIRouter(prefix="/api/notifications", tags=["Notificaciones"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_token(
    payload: TokenRegisterRequest,
    db: AsyncSession = Depends(get_db),
    # Assuming authentication dependency exists; optional for simplicity
):
    # Upsert token for user
    stmt = select(NotificationToken).where(NotificationToken.user_id == payload.user_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        await db.execute(
            update(NotificationToken)
            .where(NotificationToken.id == existing.id)
            .values(device_token=payload.device_token)
        )
    else:
        await db.execute(
            insert(NotificationToken).values(user_id=payload.user_id, device_token=payload.device_token)
        )
    await db.commit()
    return {"detail": "Token registered"}

