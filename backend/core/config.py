import os
from pydantic_settings import BaseSettings

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Diagramador Real-Time API"
    SECRET_KEY: str = "supersecretkey_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:5173"
    DEPLOYER_URL: str = "http://localhost:8081"
    
    # Base de datos
    DB_IP: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "diagramador"
    
    # Configuración de Correo para OTP
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    
    # Configuración de IA
    GEMINI_API: str = ""
    OPENROUTE_API: str = ""
    IA_MODEL: str = "cohere/north-mini-code:free"
    IMAGE_OPEROUTE_API: str = ""

    # GitHub OAuth y Seguridad
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    ENCRYPTION_MASTER_KEY: str = ""

    # Dominio publico donde se sirven las apps desplegadas (ej: https://host.gerlextech.com)
    HOST_DOMAIN: str = "http://localhost"

    @property
    def EFFECTIVE_HOST_DOMAIN(self) -> str:
        if self.HOST_DOMAIN and self.HOST_DOMAIN != "http://localhost":
            return self.HOST_DOMAIN.rstrip("/")
        if self.DEPLOYER_URL and "localhost" not in self.DEPLOYER_URL:
            from urllib.parse import urlparse
            parsed = urlparse(self.DEPLOYER_URL)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        return self.HOST_DOMAIN.rstrip("/")

    @property
    def DATABASE_URL(self) -> str:
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"postgresql+asyncpg://{self.DB_USER}:{encoded_password}@{self.DB_IP}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = env_path

settings = Settings()
