import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario, UsuarioGitHub
from backend.modules.gestion_usuarios.configurar_perfil.schemas.config_schemas import ConfiguracionResponse, ConfigurarDbRequest, PerfilRequest
from backend.modules.gestion_usuarios.recuperar_password.services.reset_service import generar_y_guardar_otp, verificar_otp
from backend.core.security import encriptar_dato

logger = logging.getLogger("uvicorn.error")

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
        email=user.email if user else None,
        nombre=user.nombre if user else None,
        # CU05: las habilidades guardadas se precargan (antes la pantalla empezaba vacía y al
        # guardar se perdían las anteriores)
        etiquetas_habilidades=[str(e) for e in (user.etiquetas_habilidades or [])] if user else [],
    )


@router.put("/perfil", response_model=ConfiguracionResponse)
async def actualizar_perfil(
    req: PerfilRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """CU05: el usuario cambia su nombre."""
    nombre = " ".join(req.nombre.split())
    if len(nombre) < 2:
        raise HTTPException(status_code=422, detail="El nombre debe tener al menos 2 caracteres.")
    user = await db.get(Usuario, current_user.id)
    user.nombre = nombre
    await db.commit()
    return await obtener_configuracion(current_user=current_user, db=db)

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
    alter_role_sql = text(f'DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = \'{owner_prefix}\') THEN CREATE ROLE "{owner_prefix}" WITH LOGIN ENCRYPTED PASSWORD \'{clean_password}\'; ELSE ALTER ROLE "{owner_prefix}" WITH PASSWORD \'{clean_password}\'; END IF; END $$;')
    try:
        # SAVEPOINT: antes el error se "ignoraba" pero dejaba la transacción abortada y el
        # UPDATE siguiente fallaba con 500 (InFailedSQLTransactionError).
        async with db.begin_nested():
            await db.execute(alter_role_sql)
    except Exception as e:
        await db.rollback()
        sin_permiso = "CREATEROLE" in str(e) or "permission denied" in str(e).lower()
        logger.warning("No se pudo crear/alterar el rol de Postgres '%s': %s", owner_prefix, type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("El servidor no tiene permiso para crear usuarios de PostgreSQL (falta CREATEROLE). "
                    "Avisa al administrador; tu contraseña no se cambió." if sin_permiso else
                    "No se pudo actualizar tu usuario de PostgreSQL en el servidor; tu contraseña no se cambió."),
        )

    await db.commit()
    
    return {"status": "success", "message": "Contraseña de base de datos actualizada en el host correctamente"}

@router.delete("/github")
async def desvincular_github(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == current_user.id))
    github = result.scalars().first()
    if github:
        await db.delete(github)
        await db.commit()
        return {"status": "success", "message": "Cuenta de GitHub desvinculada exitosamente"}
    raise HTTPException(status_code=404, detail="No posees una cuenta de GitHub vinculada.")


