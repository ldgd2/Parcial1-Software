from pydantic import BaseModel

class TokenRegisterRequest(BaseModel):
    user_id: int
    device_token: str

