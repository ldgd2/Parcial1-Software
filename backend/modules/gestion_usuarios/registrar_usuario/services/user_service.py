from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import datetime
import random
import string
from backend.modules.gestion_usuarios.registrar_usuario.schemas.request import UsuarioCreate
from backend.modules.gestion_usuarios.registrar_usuario.schemas.response import UsuarioResponse
from backend.modules.gestion_usuarios.registrar_usuario.repositories.user_repo import user_repo
from backend.modules.gestion_usuarios.models import OTPCode
from backend.modules.gestion_usuarios.recuperar_password.services.reset_service import enviar_email_otp

async def solicitar_otp_registro(email: str, db: AsyncSession):
    # Verificamos si el email ya está registrado
    db_user = await user_repo.get_by(db, email=email)
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # Eliminar OTPs anteriores
    result_otp = await db.execute(select(OTPCode).where(OTPCode.email == email))
    for otp in result_otp.scalars().all():
        await db.delete(otp)

    # Generar OTP
    codigo = "".join(random.choices(string.digits, k=6))
    expira_en = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    
    nuevo_otp = OTPCode(email=email, codigo=codigo, expira_en=expira_en)
    db.add(nuevo_otp)
    await db.commit()

    await enviar_email_otp(email, codigo)
    return {"message": "Código enviado exitosamente"}

async def registrar_nuevo_usuario(user: UsuarioCreate, db: AsyncSession) -> UsuarioResponse:
    db_user = await user_repo.get_by(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Verificar OTP
    result = await db.execute(select(OTPCode).where(OTPCode.email == user.email, OTPCode.codigo == user.codigo_otp))
    otp = result.scalars().first()

    if not otp or datetime.datetime.utcnow() > otp.expira_en:
        raise HTTPException(status_code=400, detail="Código inválido o expirado.")

    new_user = await user_repo.create_user(db=db, user=user)
    
    await db.delete(otp)
    await db.commit()

    return UsuarioResponse.model_validate(new_user)
