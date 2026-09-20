from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.database import get_db
from backend.modules.gestion_proyectos.models import Proyecto

router = APIRouter(prefix="/deploy-callback", tags=["Despliegue Callback"])

class DeployCallbackRequest(BaseModel):
    project_id: int
    deployment_url: str

@router.post("")
async def update_deployment_status(
    payload: DeployCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe la URL (o puerto) de despliegue desde el servidor Deployer 
    y actualiza la base de datos del proyecto principal.
    """
    result = await db.execute(select(Proyecto).where(Proyecto.id == payload.project_id))
    proyecto = result.scalars().first()
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    proyecto.deployment_url = payload.deployment_url
    await db.commit()
    
    return {"status": "ok", "message": "Deployment URL actualizada con éxito"}
