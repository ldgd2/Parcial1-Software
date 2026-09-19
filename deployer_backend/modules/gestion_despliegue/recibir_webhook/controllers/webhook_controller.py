from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from ..schemas.webhook_schemas import WebhookPayload, DeployResponse
from ..services.deploy_service import deploy_project

router = APIRouter(prefix="/deploy", tags=["Despliegue Automático"])

@router.post("/webhook", response_model=DeployResponse)
async def webhook_deploy(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Execute deployment in background to not block the webhook response
    background_tasks.add_task(deploy_project, payload.repo_url, payload.project_id, db)
    
    return DeployResponse(
        status="accepted",
        message=f"Despliegue iniciado en background para proyecto {payload.project_id}",
    )
