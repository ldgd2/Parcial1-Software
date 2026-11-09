import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK once at import time
# Path to service account key JSON file – configure via environment variable or config
import os
service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT', 'path/to/serviceAccountKey.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)

def send_fcm_message(token: str, title: str, body: str, data: dict | None = None) -> str:
    """Send a push notification via Firebase Cloud Messaging.
    Returns the message ID returned by FCM.
    """
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {}
    )
    response = messaging.send(message)
    return response

