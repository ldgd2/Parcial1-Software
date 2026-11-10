import datetime
import hashlib

from jose import jwt
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.modules.gestion_usuarios.cerrar_sesion.schemas.response import MessageResponse
from backend.modules.gestion_usuarios.models import TokenRevocado


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def procesar_cierre_sesion(db: AsyncSession, token: str) -> MessageResponse:
    """CU03: el token deja de ser válido en el servidor (antes seguía funcionando hasta expirar)."""
    ahora = datetime.datetime.utcnow()
    try:
        exp = jwt.get_unverified_claims(token).get("exp")
        expira = datetime.datetime.utcfromtimestamp(exp) if exp else ahora + datetime.timedelta(days=1)
    except Exception:
        expira = ahora + datetime.timedelta(days=1)

    # Limpieza de revocaciones ya vencidas (el JWT también estaría vencido)
    await db.execute(delete(TokenRevocado).where(TokenRevocado.expira_en < ahora))
    if await db.get(TokenRevocado, hash_token(token)) is None:
        db.add(TokenRevocado(token_hash=hash_token(token), expira_en=expira))
    await db.commit()
    return MessageResponse(message="Sesión cerrada correctamente.")
