from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import init_db
from modules.gestion_despliegue.recibir_webhook.controllers import webhook_controller
import uvicorn
import asyncio

from modules.gestion_despliegue.recibir_webhook.services.deploy_service import auto_fix_all_databases

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_controller.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def on_startup():
    await init_db()
    try:
        auto_fix_all_databases()
    except Exception as e:
        print(f"Startup DB permissions fix warning: {e}")
    print(f"Deployer Backend started. Workspace: {settings.WORKSPACE_DIR}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
