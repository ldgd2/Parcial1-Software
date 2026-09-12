import random
import string
import datetime
import yagmail
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from backend.core.config import settings
from backend.modules.gestion_usuarios.models import OTPCode, Usuario
from backend.core.security import get_password_hash

def _enviar_email_yagmail(destinatario: str, codigo: str):
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        print(f"DEBUG: OTP para {destinatario} es {codigo} (No enviado, faltan credenciales Gmail)")
        return
        
    try:
        yag = yagmail.SMTP(user=settings.GMAIL_USER, password=settings.GMAIL_APP_PASSWORD)
        asunto = "Código de Recuperación de Contraseña"
        contenido = f"Tu código de recuperación es: {codigo}\n\nEste código expira en 5 minutos."
        yag.send(to=destinatario, subject=asunto, contents=contenido)
    except Exception as e:
        print(f"Error al enviar correo con yagmail: {e}")
        raise HTTPException(status_code=500, detail="No se pudo enviar el correo.")

async def enviar_email_otp(destinatario: str, codigo: str):
    await asyncio.to_thread(_enviar_email_yagmail, destinatario, codigo)

async def generar_y_guardar_otp(email: str, db: AsyncSession):
    # Verificar si el usuario existe
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    user = result.scalars().first()
    if not user:
        # Por seguridad no revelamos que no existe, pero detenemos acá (o podríamos simular)
        return {"message": "Si el correo está registrado, se enviará un código."}

    # Eliminar OTPs anteriores de este email
    result_otp = await db.execute(select(OTPCode).where(OTPCode.email == email))
    old_otps = result_otp.scalars().all()
    for otp in old_otps:
        await db.delete(otp)

    # Generar nuevo OTP
    codigo = "".join(random.choices(string.digits, k=6))
    expira_en = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    
    nuevo_otp = OTPCode(email=email, codigo=codigo, expira_en=expira_en)
    db.add(nuevo_otp)
    await db.commit()

    # Enviar correo
    await enviar_email_otp(email, codigo)
        
    return {"message": "Si el correo está registrado, se enviará un código."}

async def verificar_otp(email: str, codigo: str, db: AsyncSession):
    result = await db.execute(select(OTPCode).where(OTPCode.email == email, OTPCode.codigo == codigo))
    otp = result.scalars().first()

    if not otp:
        raise HTTPException(status_code=400, detail="Código inválido.")

    if datetime.datetime.utcnow() > otp.expira_en:
        await db.delete(otp)
        await db.commit()
        raise HTTPException(status_code=400, detail="El código ha expirado.")

    return {"message": "Código verificado exitosamente."}

async def restablecer_password(email: str, codigo: str, nueva_password: str, db: AsyncSession):
    # Primero verificamos el OTP nuevamente por seguridad
    result = await db.execute(select(OTPCode).where(OTPCode.email == email, OTPCode.codigo == codigo))
    otp = result.scalars().first()

    if not otp or datetime.datetime.utcnow() > otp.expira_en:
        raise HTTPException(status_code=400, detail="Código inválido o expirado.")

    # Actualizar contraseña
    user_result = await db.execute(select(Usuario).where(Usuario.email == email))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user.hashed_password = get_password_hash(nueva_password)
    
    # Eliminar OTP usado
    await db.delete(otp)
    await db.commit()

    return {"message": "Contraseña actualizada exitosamente."}
