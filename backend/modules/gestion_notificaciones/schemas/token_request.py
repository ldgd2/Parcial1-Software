from typing import Optional

from pydantic import BaseModel

class TokenRegisterRequest(BaseModel):
    # Opcional: el usuario sale de la sesión. Si se manda, debe coincidir con ella.
    user_id: Optional[int] = None
    device_token: str
