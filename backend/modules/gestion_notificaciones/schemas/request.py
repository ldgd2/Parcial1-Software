from pydantic import BaseModel
from typing import Optional, Dict

class NotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str
    data: Optional[Dict[str, str]] = None

