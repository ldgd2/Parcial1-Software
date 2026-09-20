from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario, UsuarioGitHub
from backend.modules.gestion_usuarios.configurar_perfil.schemas.config_schemas import ConfiguracionResponse, ConfigurarDbRequest
from backend.core.security import encriptar_dato

router = APIRouter(prefix="/configuracion", tags=["Configuracion de Perfil"])

@router.get("", response_model=ConfiguracionResponse)
async def obtener_configuracion(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Buscar si tiene GitHub
    result = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == current_user.id))
    github = result.scalars().first()
    
    # Su registro actual ya tiene si la DB está configurada
    result_user = await db.execute(select(Usuario).where(Usuario.id == current_user.id))
    user = result_user.scalars().first()
    
    return ConfiguracionResponse(
        github_vinculado=github is not None,
        github_username=github.github_username if github else None,
        db_configurada=user.db_password_encrypted is not None if user else False
    )

@router.post("/db")
async def configurar_db_password(
    payload: ConfigurarDbRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result_user = await db.execute(select(Usuario).where(Usuario.id == current_user.id))
    user = result_user.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    user.db_password_encrypted = encriptar_dato(payload.db_password)
    await db.commit()
    
    return {"status": "success", "message": "Contraseña de base de datos actualizada"}
