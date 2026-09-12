from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_usuarios.iniciar_sesion.schemas.request import LoginRequest, AnonimoCreate
from backend.modules.gestion_usuarios.iniciar_sesion.schemas.response import TokenResponse
from backend.modules.gestion_usuarios.iniciar_sesion.repositories.login_repo import login_repo
from backend.core.security import verify_password, create_access_token

async def autenticar_usuario(login_data: LoginRequest, db: AsyncSession) -> TokenResponse:
    user = await login_repo.get_by(db, email=login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "rol_global": "registrado"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")

async def registrar_ingreso_anonimo(data: AnonimoCreate, db: AsyncSession) -> TokenResponse:
    user = await login_repo.create_anonimo(db, data)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "rol_global": "anonimo"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
