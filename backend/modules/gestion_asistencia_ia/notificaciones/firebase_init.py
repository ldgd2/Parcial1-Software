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
    local_config = Path(__file__).parent / "config" / "diagramador-firebase-service.json"
    backend_root = Path(__file__).resolve().parents[4]
    
    candidates = [
        Path(env_path) if env_path else None,
        local_config,
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

    print("[firebase_init] AVISO: No se encontraron credenciales de Firebase válidas. Push notifications estarán deshabilitadas.")
    return False

_init_firebase()


def send_fcm_message(token: str, title: str, body: str, data: Optional[dict] = None) -> str:
    """Send a push notification via Firebase Cloud Messaging.
    Returns the message ID returned by FCM.
    """
    if not firebase_admin._apps:
        if not _init_firebase():
            raise RuntimeError("Firebase Admin no está configurado.")

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {},
    )
    response = messaging.send(message)
    return response
