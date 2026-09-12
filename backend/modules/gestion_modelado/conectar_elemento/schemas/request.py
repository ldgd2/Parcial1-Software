from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

RelationType = Literal[
    "association", "inheritance", "composition",
    "aggregation", "dependency", "realization", "directed"
]


class ConectarElementoRequest(BaseModel):
    id: str
    proyecto_id: int
    type: RelationType
    source_id: str
    target_id: str
    label: str = ""
    source_label: str = ""
    target_label: str = ""
    version: int = 0
    hash: str = ""


class RelacionResponse(BaseModel):
    id: str
    proyecto_id: int
    type: RelationType
    source_id: str
    target_id: str
    label: Optional[str]
    source_label: Optional[str]
    target_label: Optional[str]
    version: int
    hash: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
