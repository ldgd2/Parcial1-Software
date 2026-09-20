import os
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # API configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Deployer Backend"

    # Workspace for cloning repositories
    WORKSPACE_DIR: str = str(Path(__file__).parent.parent / "workspace")
    
    # Internal DB (SQLite for tracking deployments and processes)
    DATABASE_URL: str = "sqlite+aiosqlite:///./deployer.db"
    
    # External DB (Main Backend DB - PostgreSQL)
    MAIN_DB_URL: str = os.getenv("MAIN_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost/diagramador_db")
    
    # Base domain/IP for deployed projects
    BASE_DOMAIN: str = os.getenv("BASE_DOMAIN", "http://localhost")
    
    # PostgreSQL Admin Password
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "postgres")
    
    # PostgreSQL Host (for provisioning DBs for deployed Spring Boot apps)
    PG_HOST: str = "127.0.0.1"
    
    # Main API URL (for callbacks to the diagramador backend)
    MAIN_API_URL: str = "http://localhost:8000"
    
    # Public domain for deployed apps
    SERVER_DOMAIN: str = "http://localhost"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure workspace exists
os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
