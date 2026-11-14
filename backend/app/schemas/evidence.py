
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    evidence_id: str
    evidence_type: str
    evidence_reference: str
    description: str
    content_hash: Optional[str] = None
    version: int
    added_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    evidence: list[EvidenceResponse]
