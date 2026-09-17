from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os

from backend.modules.gestion_asistencia_ia.exportar_github.schemas.exportar_schemas import GithubAuthCallback, ExportarProyectoRequest, ExportarProyectoResponse
from backend.modules.gestion_asistencia_ia.exportar_github.services.github_service import vincular_cuenta_github, crear_repo_github
from backend.modules.gestion_asistencia_ia.exportar_github.services.git_service import subir_codigo_a_github
from backend.modules.gestion_asistencia_ia.exportar_github.services.generacion_service import generar_spring_boot

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario, UsuarioGitHub
from backend.core.security import desencriptar_dato

router = APIRouter(prefix="/exportar-github", tags=["Exportar a GitHub"])

@router.get("/status")
async def get_github_status(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verifica si el usuario tiene una cuenta de GitHub vinculada."""
    result = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == current_user.id))
    vinculo = result.scalars().first()
    
    if vinculo:
        return {"vinculado": True, "github_username": vinculo.github_username}
    return {"vinculado": False}

@router.get("/auth-url")
async def get_auth_url(current_user: Usuario = Depends(get_current_user)):
    """Devuelve la URL de autorización de GitHub para que el frontend redirija al usuario."""
    from backend.core.config import settings
    client_id = settings.GITHUB_CLIENT_ID
    if not client_id:
        raise HTTPException(status_code=500, detail="Falta GITHUB_CLIENT_ID en el servidor.")
    
    redirect_uri = "http://localhost:5173/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=repo&redirect_uri={redirect_uri}"
    return {"url": url}

@router.post("/callback")
async def github_callback(
    payload: GithubAuthCallback,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recibe el code de GitHub y lo vincula con el usuario actual."""
    github_username = await vincular_cuenta_github(current_user.id, payload.code, db)
    return {"mensaje": "Cuenta vinculada con éxito", "github_username": github_username}

@router.post("/exportar", response_model=ExportarProyectoResponse)
async def exportar_proyecto(
    payload: ExportarProyectoRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exporta el proyecto usando el token guardado en la base de datos.
    """
    try:
        # 1. Buscamos el vínculo en la BD
        result = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == current_user.id))
        vinculo = result.scalars().first()
        
        if not vinculo:
            raise HTTPException(status_code=400, detail="Debes vincular tu cuenta de GitHub primero.")
            
        # 2. Desencriptamos el token
        token_real = desencriptar_dato(vinculo.encrypted_token)
        
        # 3. Generar código en carpeta temporal
        carpeta_temporal = await generar_spring_boot(payload.diagram_json)
        
        # 4. Crear repositorio en GitHub
        url_repositorio = await crear_repo_github(token_real, payload.nombre_repo)
        
        # 5. Hacer push con Git
        subir_codigo_a_github(carpeta_temporal, url_repositorio, token_real)
        
        return ExportarProyectoResponse(
            url_repositorio=url_repositorio,
            mensaje=f"¡Éxito! Tu código está en: {url_repositorio}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la exportación: {str(e)}")
