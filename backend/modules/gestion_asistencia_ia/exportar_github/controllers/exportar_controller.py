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
    
    redirect_uri = f"{settings.FRONTEND_URL}/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=repo,user&redirect_uri={redirect_uri}"
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
    Si ya tiene repositorio vinculado, hace commit con IA y push.
    """
    try:
        # 1. Buscamos el proyecto y al anfitrión
        from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
        result_proj = await db.execute(select(Proyecto).where(Proyecto.id == payload.proyecto_id))
        proyecto = result_proj.scalars().first()
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

        # Buscar al anfitrión
        result_colab = await db.execute(
            select(ColaboradorProyecto).where(
                (ColaboradorProyecto.proyecto_id == payload.proyecto_id) & 
                (ColaboradorProyecto.rol_proyecto == "anfitrion")
            )
        )
        anfitrion_colab = result_colab.scalars().first()
        if not anfitrion_colab:
            raise HTTPException(status_code=500, detail="Error: El proyecto no tiene un anfitrión válido.")
            
        anfitrion_id = anfitrion_colab.usuario_id
        
        # Obtener el Usuario anfitrión
        result_user = await db.execute(select(Usuario).where(Usuario.id == anfitrion_id))
        anfitrion = result_user.scalars().first()

        # 2. Buscamos el vínculo con GitHub del anfitrión
        result_gh = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == anfitrion_id))
        vinculo = result_gh.scalars().first()
        
        if not vinculo:
            raise HTTPException(status_code=400, detail="El anfitrión del proyecto aún no ha vinculado su cuenta de GitHub en Configuración.")
            
        if payload.auto_deploy and not anfitrion.db_password_encrypted:
            raise HTTPException(status_code=400, detail="El anfitrión del proyecto no ha configurado una contraseña de Base de Datos para el auto-alojamiento. (Dile que vaya al engranaje en su Dashboard)")

        # 3. Desencriptamos tokens
        token_real = desencriptar_dato(vinculo.encrypted_token)
        db_password = desencriptar_dato(anfitrion.db_password_encrypted) if anfitrion.db_password_encrypted else "password"
        
        # 4. Generar código en carpeta temporal
        if proyecto.github_repo_url:
            # Ignorar "update" del frontend y extraer el nombre real del repo desde la URL
            real_repo_name = proyecto.github_repo_url.split('/')[-1].replace('.git', '')
            payload.nombre_repo = real_repo_name

        db_name = payload.nombre_repo.lower().replace("-", "_")
        
        owner_prefix = anfitrion.email.split("@")[0] if anfitrion.email else "user"
        if payload.auto_deploy:
            from backend.core.config import settings
            url_base = f"{settings.HOST_DOMAIN}/host/{owner_prefix}/{db_name}"
        else:
            url_base = "http://localhost:8080"
            
        carpeta_temporal, api_docs_md = await generar_spring_boot(payload.diagram_json, payload.nombre_repo, db_password, url_base)
        
        if proyecto.github_repo_url:
            # 5a. Ya tiene repo: Actualizar código
            from backend.modules.gestion_asistencia_ia.exportar_github.services.git_service import actualizar_codigo_en_github
            mensaje = await actualizar_codigo_en_github(carpeta_temporal, proyecto.github_repo_url, token_real)
            
            if payload.auto_deploy:
                # Notificar al webhook (asíncrono, no bloqueante) con URL autenticada
                url_auth = proyecto.github_repo_url.replace("https://", f"https://x-access-token:{token_real}@")
                from backend.modules.gestion_proyectos.notificar_despliegue.services.webhook_service import notificar_deployer
                import asyncio
                asyncio.create_task(notificar_deployer(proyecto.id, url_auth, db_name, db_password, owner_prefix))

            return ExportarProyectoResponse(
                url_repositorio=proyecto.github_repo_url,
                mensaje=f"Código actualizado en GitHub. {'Despliegue iniciado.' if payload.auto_deploy else ''} Detalle: {mensaje}",
                api_docs_md=api_docs_md
            )
        else:
            # 5b. No tiene repo: Crear y subir inicial
            url_repositorio = await crear_repo_github(token_real, payload.nombre_repo)
            subir_codigo_a_github(carpeta_temporal, url_repositorio, token_real)
            
            # Guardar la URL en el proyecto
            proyecto.github_repo_url = url_repositorio
            await db.commit()
            
            if payload.auto_deploy:
                # Notificar al webhook (asíncrono, no bloqueante) con URL autenticada
                url_auth = url_repositorio.replace("https://", f"https://x-access-token:{token_real}@")
                from backend.modules.gestion_proyectos.notificar_despliegue.services.webhook_service import notificar_deployer
                import asyncio
                asyncio.create_task(notificar_deployer(proyecto.id, url_auth, db_name, db_password, owner_prefix))
            
            return ExportarProyectoResponse(
                url_repositorio=url_repositorio,
                mensaje=f"¡Éxito! Tu código está en: {url_repositorio}. {'Y el despliegue se ha iniciado.' if payload.auto_deploy else ''}",
                api_docs_md=api_docs_md
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la exportación: {str(e)}")
