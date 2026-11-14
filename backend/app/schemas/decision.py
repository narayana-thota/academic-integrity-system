from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


ALLOWED_DECISION_TYPES = {
    "NO_VIOLATION",
    "ACADEMIC_MISCONDUCT",
    "INSUFFICIENT_EVIDENCE",
    "REQUEST_MORE_EVIDENCE",
}


class DecisionCreateRequest(BaseModel):
    reviewer_id: int = Field(gt=0)
    decision_type: str
    rationale: str = Field(min_length=10, max_length=10000)

    model_config = {"str_strip_whitespace": True}


class DecisionResponse(BaseModel):
    decision_id: int
    case_id: str
    reviewer_id: int
    reviewer_name: Optional[str] = None
    decision_type: str
    decision_stage: str
    rationale: str
    decided_at: datetime
    supersedes_decision_id: Optional[int] = None


class DecisionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    decisions: list[DecisionResponse]