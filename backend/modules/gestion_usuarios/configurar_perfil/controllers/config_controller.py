import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario, UsuarioGitHub
from backend.modules.gestion_usuarios.configurar_perfil.schemas.config_schemas import ConfiguracionResponse, ConfigurarDbRequest
from backend.modules.gestion_usuarios.recuperar_password.services.reset_service import generar_y_guardar_otp, verificar_otp
from backend.core.security import encriptar_dato

router = APIRouter(prefix="/configuracion", tags=["Configuracion de Perfil"])

@router.get("", response_model=ConfiguracionResponse)
async def obtener_configuracion(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == current_user.id))
    github = result.scalars().first()
    
    result_user = await db.execute(select(Usuario).where(Usuario.id == current_user.id))
    user = result_user.scalars().first()
    
    return ConfiguracionResponse(
        github_vinculado=github is not None,
        github_username=github.github_username if github else None,
        db_configurada=user.db_password_encrypted is not None if user else False,
        email=user.email if user else None
    )

@router.post("/solicitar-otp")
async def solicitar_otp_db(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.email:
        raise HTTPException(status_code=400, detail="El usuario no posee un email registrado.")
    
    return await generar_y_guardar_otp(current_user.email, db)

@router.post("/db")
async def configurar_db_password(
    payload: ConfigurarDbRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not payload.codigo_otp or not payload.codigo_otp.strip():
        raise HTTPException(status_code=400, detail="Debes ingresar el código OTP recibido en tu correo.")
        
    if not payload.db_password or len(payload.db_password.strip()) < 4:
        raise HTTPException(status_code=400, detail="La contraseña debe contener al menos 4 caracteres.")

    # 1. Verificar OTP
    await verificar_otp(current_user.email, payload.codigo_otp.strip(), db)
    
    # 2. Actualizar en el modelo Usuario
    result_user = await db.execute(select(Usuario).where(Usuario.id == current_user.id))
    user = result_user.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    user.db_password_encrypted = encriptar_dato(payload.db_password)
    
    # 3. Alterar contraseña de ROL en Postgres en el host
    owner_prefix = re.sub(r'[^a-zA-Z0-9]', '', user.email.split("@")[0]) if user.email else "user"
    clean_password = payload.db_password.replace("'", "''")
    try:
        alter_role_sql = text(f'DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = \'{owner_prefix}\') THEN CREATE ROLE "{owner_prefix}" WITH LOGIN ENCRYPTED PASSWORD \'{clean_password}\'; ELSE ALTER ROLE "{owner_prefix}" WITH PASSWORD \'{clean_password}\'; END IF; END $$;')
        await db.execute(alter_role_sql)
    except Exception as e:
        print(f"Advertencia al ejecutar ALTER ROLE en Postgres: {e}")

    await db.commit()
    
    return {"status": "success", "message": "Contraseña de base de datos actualizada en el host correctamente"}

