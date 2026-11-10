import os
from pydantic_settings import BaseSettings

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Diagramador Real-Time API"
    SECRET_KEY: str = "supersecretkey_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:5173"
    SQL_ECHO: bool = False   # log de cada consulta SQL (solo para depurar)
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
    AI_PROVIDER: str = "gemini"  # "gemini" | "openrouter" | "kimi"
    GEMINI_API: str = ""
    OPENROUTE_API: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-exp:free"
    OPENROUTER_VISION_MODEL: str = "google/gemini-2.0-flash-exp:free"
    KIMI_API: str = ""
    KIMI_MODEL: str = "kimi-k3.1-pro"
    KIMI_VISION_MODEL: str = "kimi-k3.1-pro"
    IA_MODEL: str = "cohere/north-mini-code:free"
    IMAGE_OPEROUTE_API: str = ""

    # GitHub OAuth y Seguridad
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    ENCRYPTION_MASTER_KEY: str = ""

    # Dominio publico donde se sirven las apps desplegadas (ej: https://host.gerlextech.com)
    HOST_DOMAIN: str = "http://localhost"

    # CU39: notificaciones push con Firebase (opcional: sin esto solo hay notificaciones dentro de la app)
    FIREBASE_CREDENTIALS: str = ""      # ruta al JSON de la cuenta de servicio (Configuración > Cuentas de servicio)
    FIREBASE_WEB_API_KEY: str = ""      # Configuración del proyecto > Tus apps > Web
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SENDER_ID: str = ""
    FIREBASE_APP_ID: str = ""
    FIREBASE_VAPID_KEY: str = ""        # Cloud Messaging > Certificados push web

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
