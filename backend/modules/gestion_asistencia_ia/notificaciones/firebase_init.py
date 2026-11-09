import os
from pathlib import Path
from typing import Optional
import firebase_admin
from firebase_admin import credentials, messaging

_firebase_initialized = False

def _init_firebase() -> bool:
    global _firebase_initialized
    if firebase_admin._apps:
        _firebase_initialized = True
        return True

    env_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    config_dir = Path(__file__).resolve().parent / "config"
    backend_root = Path(__file__).resolve().parents[4]

    # Detectar cualquier archivo .json que el usuario haya subido a la carpeta config
    json_in_config = list(config_dir.glob("*.json")) if config_dir.is_dir() else []

    candidates = [
        Path(env_path) if env_path else None,
        *json_in_config,
        config_dir / "diagramador-firebase-service.json",
        backend_root / "backend" / "firebase-service-account.json",
        backend_root / "firebase-service-account.json",
    ]

    for candidate in candidates:
        if candidate and candidate.is_file():
            try:
                cred = credentials.Certificate(str(candidate))
                firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                print(f"[firebase_init] Firebase Admin inicializado con: {candidate}")
                return True
            except Exception as e:
                print(f"[firebase_init] Error al inicializar Firebase con {candidate}: {e}")

    print("[firebase_init] AVISO: No se encontraron credenciales de Firebase validas. Push notifications estaran deshabilitadas.")
    return False

_init_firebase()


def send_fcm_message(token: str, title: str, body: str, data: Optional[dict] = None) -> str:
    """Send a push notification via Firebase Cloud Messaging.
    Returns the message ID returned by FCM.
    """
    if not firebase_admin._apps:
        if not _init_firebase():
            raise RuntimeError("Firebase Admin no esta configurado.")

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {},
    )
    response = messaging.send(message)
    return response
