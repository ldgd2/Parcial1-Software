import httpx
import os
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.modules.gestion_usuarios.models import UsuarioGitHub
from backend.core.security import encriptar_dato

async def vincular_cuenta_github(usuario_id: int, codigo: str, db: AsyncSession) -> str:
    """Intercambia el código temporal por un Access Token, obtiene el usuario de GitHub y lo guarda en BD."""
    from backend.core.config import settings
    client_id = settings.GITHUB_CLIENT_ID
    client_secret = settings.GITHUB_CLIENT_SECRET
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Configuración de GitHub OAuth incompleta en el servidor.")

    # 1. Obtener Access Token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": codigo,
                "redirect_uri": f"{settings.FRONTEND_URL}/github/callback"
            },
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al comunicarse con GitHub para obtener el token.")
            
        data = response.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=f"Error de GitHub: {data.get('error_description')}")
            
        access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub no devolvió un token de acceso válido.")

    # 2. Obtener el nombre de usuario de GitHub
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al obtener el perfil de GitHub.")
            
        github_username = user_response.json().get("login")

    # 3. Encriptar y Guardar
    token_cifrado = encriptar_dato(access_token)
    
    # Revisar si ya tiene vinculada una cuenta
    result = await db.execute(select(UsuarioGitHub).where(UsuarioGitHub.usuario_id == usuario_id))
    vinculo = result.scalars().first()
    
    if vinculo:
        vinculo.github_username = github_username
        vinculo.encrypted_token = token_cifrado
    else:
        vinculo = UsuarioGitHub(
            usuario_id=usuario_id,
            github_username=github_username,
            encrypted_token=token_cifrado
        )
        db.add(vinculo)
        
    await db.commit()
    
    return github_username

async def crear_repo_github(token: str, nombre_repo: str) -> str:
    """Crea un repositorio vacío en la cuenta del usuario y devuelve la URL del repositorio."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "name": nombre_repo,
        "private": True,
        "auto_init": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.github.com/user/repos", json=data, headers=headers)
        
        if response.status_code not in (201, 200):
            raise HTTPException(status_code=response.status_code, detail=f"Error al crear el repositorio: {response.text}")
            
        return response.json()["clone_url"]
