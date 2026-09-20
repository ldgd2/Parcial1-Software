from pydantic import BaseModel

class WebhookPayload(BaseModel):
    project_id: int
    repo_url: str
    db_name: str | None = None
    db_password: str | None = None
    owner_prefix: str | None = None

class DeployResponse(BaseModel):
    status: str
    message: str
    deployment_url: str | None = None
