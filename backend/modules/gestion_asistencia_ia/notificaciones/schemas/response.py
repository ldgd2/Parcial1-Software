from pydantic import BaseModel
from typing import Optional

class NotificationResponse(BaseModel):
    message_id: str
    detail: Optional[str] = None

