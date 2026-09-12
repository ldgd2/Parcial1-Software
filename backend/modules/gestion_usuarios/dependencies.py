from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.core.database import get_db
from backend.modules.gestion_usuarios.models import Usuario
from backend.core.repository import BaseRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login")
user_repo = BaseRepository(Usuario)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        rol_global: str = payload.get("rol_global")
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await user_repo.get(db, id=int(user_id_str))
    if user is None:
        raise credentials_exception
        
    # Guardamos el rol decodificado en el objeto para poder chequearlo después
    user.rol_global = rol_global
    return user


