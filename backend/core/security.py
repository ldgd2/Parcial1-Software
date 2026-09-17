from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Encriptación de datos sensibles (Fernet) ---
from cryptography.fernet import Fernet
import os
import base64

def get_fernet_instance():
    from backend.core.config import settings
    key = settings.ENCRYPTION_MASTER_KEY
    if not key:
        key = Fernet.generate_key().decode()
        print("WARNING: ENCRYPTION_MASTER_KEY no está definida en .env. Usando llave temporal.")
    
    try:
        return Fernet(key.encode())
    except ValueError:
        print("ERROR: ENCRYPTION_MASTER_KEY no es válida. Debe ser url-safe base64-encoded de 32 bytes.")
        return Fernet(Fernet.generate_key())

fernet = get_fernet_instance()

def encriptar_dato(texto_plano: str) -> str:
    if not texto_plano:
        return ""
    return fernet.encrypt(texto_plano.encode()).decode()

def desencriptar_dato(texto_cifrado: str) -> str:
    if not texto_cifrado:
        return ""
    return fernet.decrypt(texto_cifrado.encode()).decode()
