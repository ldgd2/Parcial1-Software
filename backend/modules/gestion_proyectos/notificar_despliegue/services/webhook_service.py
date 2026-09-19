import httpx
from fastapi import HTTPException
import os

DEPLOYER_URL = os.getenv("DEPLOYER_URL", "http://localhost:8001/api/v1/deploy/webhook")

async def notificar_deployer(project_id: int, repo_url: str):
    """
    Envía una petición POST al Deployer Backend para que inicie el proceso de despliegue.
    """
    payload = {
        "project_id": project_id,
        "repo_url": repo_url
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(DEPLOYER_URL, json=payload)
            if response.status_code not in (200, 201, 202):
                print(f"Error del Deployer Backend: {response.text}")
                # No lanzamos excepción estricta para no romper el flujo principal si el deployer falla
                return {"status": "error", "detail": f"Deployer falló: {response.status_code}"}
                
            return response.json()
        except httpx.RequestError as e:
            print(f"Error conectando con Deployer Backend: {e}")
            return {"status": "error", "detail": "No se pudo contactar al servidor de despliegue."}
