import os
from pathlib import Path
from typing import Optional

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _HAS_FIREBASE_SDK = True
except ImportError:
    firebase_admin = None  # type: ignore
    credentials = None     # type: ignore
    messaging = None       # type: ignore
    _HAS_FIREBASE_SDK = False

_firebase_initialized = False


def candidatos_credenciales() -> list:
    """Rutas donde se busca el JSON de la cuenta de servicio, en orden de preferencia.
    Lo usan este módulo y notificaciones_service (avisos automáticos), así basta con poner
    el JSON en la carpeta config/ o configurar FIREBASE_CREDENTIALS / FIREBASE_SERVICE_ACCOUNT."""
    env_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    config_dir = Path(__file__).resolve().parent / "config"
    backend_root = Path(__file__).resolve().parents[3]

    # Detectar cualquier archivo .json que el usuario haya subido a la carpeta config
    json_in_config = sorted(config_dir.glob("*.json")) if config_dir.is_dir() else []

    # Carpeta anterior del módulo (gestion_asistencia_ia/notificaciones/config): quien ya tenía
    # ahí su JSON sigue funcionando sin moverlo.
    config_viejo = backend_root / "backend" / "modules" / "gestion_asistencia_ia" / "notificaciones" / "config"
    json_viejo = sorted(config_viejo.glob("*.json")) if config_viejo.is_dir() else []

    candidates = [
        Path(env_path) if env_path else None,
        *json_in_config,
        *json_viejo,
        config_dir / "diagramador-firebase-service.json",
        backend_root / "backend" / "firebase-service-account.json",
        backend_root / "firebase-service-account.json",
    ]
    try:
        from backend.core.config import settings
        ruta = (settings.FIREBASE_CREDENTIALS or "").strip()
        if ruta:
            for base in (Path(ruta), backend_root / ruta, backend_root / "backend" / ruta):
                candidates.insert(1, base)
    except Exception:
        pass
    return [c for c in candidates if c is not None]


def _init_firebase() -> bool:
    global _firebase_initialized
    if not _HAS_FIREBASE_SDK or firebase_admin is None:
        return False

    # Solo la app por defecto: notificaciones_service usa otra app con nombre propio,
    # y si se contara esa, messaging.send() fallaría por no existir la app por defecto.
    if "[DEFAULT]" in firebase_admin._apps:
        _firebase_initialized = True
        return True

    candidates = candidatos_credenciales()

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

if _HAS_FIREBASE_SDK:
    _init_firebase()


def send_fcm_message(token: str, title: str, body: str, data: Optional[dict] = None) -> str:
    """Send a push notification via Firebase Cloud Messaging.
    Returns the message ID returned by FCM.
    """
    if not _HAS_FIREBASE_SDK or messaging is None:
        raise RuntimeError("firebase-admin no esta instalado en este entorno de Python.")

    if "[DEFAULT]" not in firebase_admin._apps:
        if not _init_firebase():
            raise RuntimeError("Firebase Admin no esta configurado.")

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {},
    )
    response = messaging.send(message)
    return response
