from pydantic import BaseModel

class WebhookPayload(BaseModel):
    project_id: int
    repo_url: str

class DeployResponse(BaseModel):
    status: str
    message: str
    deployment_url: str | None = None
