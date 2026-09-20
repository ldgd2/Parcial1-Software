import httpx
from fastapi import HTTPException
from backend.core.config import settings

async def notificar_deployer(project_id: int, repo_url: str, db_name: str = None, db_password: str = None, owner_prefix: str = None):
    """
    Envía una petición POST al Deployer Backend para que inicie el proceso de despliegue.
    """
    payload = {
        "project_id": project_id,
        "repo_url": repo_url
    }
    if db_name and db_password:
        payload["db_name"] = db_name
        payload["db_password"] = db_password
    if owner_prefix:
        payload["owner_prefix"] = owner_prefix
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            webhook_url = f"{settings.DEPLOYER_URL.rstrip('/')}/api/v1/deploy/webhook"
            response = await client.post(webhook_url, json=payload)
            if response.status_code not in (200, 201, 202):
                print(f"Error del Deployer Backend: {response.text}")
                # No lanzamos excepción estricta para no romper el flujo principal si el deployer falla
                return {"status": "error", "detail": f"Deployer falló: {response.status_code}"}
                
            return response.json()
        except httpx.RequestError as e:
            print(f"Error conectando con Deployer Backend: {e}")
            return {"status": "error", "detail": "No se pudo contactar al servidor de despliegue."}
