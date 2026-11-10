from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_notificaciones.schemas.token_request import TokenRegisterRequest
from backend.modules.gestion_notificaciones.models import NotificationToken
from sqlalchemy import select

router = APIRouter(prefix="/api/notifications", tags=["Notificaciones"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_token(
    payload: TokenRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # El celular se registra SIEMPRE a nombre de la sesión: antes cualquiera podía mandar
    # el user_id de otra persona y recibir sus notificaciones.
    if payload.user_id is not None and payload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes registrar un celular para tu propia cuenta",
        )
    token = payload.device_token.strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falta el token del dispositivo")

    # El token es único: si el celular ya estaba registrado (por ejemplo, otra cuenta inició
    # sesión antes en él), pasa a la cuenta actual en vez de fallar por duplicado.
    existente = (await db.execute(
        select(NotificationToken).where(NotificationToken.device_token == token)
    )).scalar_one_or_none()
    if existente:
        existente.user_id = current_user.id
    else:
        propio = (await db.execute(
            select(NotificationToken)
            .where(NotificationToken.user_id == current_user.id)
            .order_by(NotificationToken.id.desc())
            .limit(1)
        )).scalar_one_or_none()
        if propio:
            propio.device_token = token
        else:
            db.add(NotificationToken(user_id=current_user.id, device_token=token))
    await db.commit()
    return {"detail": "Token registered"}
