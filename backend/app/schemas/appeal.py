from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AppealCreateRequest(BaseModel):
    learner_id: int
    appeal_reason: str = Field(min_length=20, max_length=5000)


class AppealResolveRequest(BaseModel):
    reviewer_id: int
    outcome: Literal["UPHELD", "OVERTURNED", "MODIFIED"]
    rationale: str = Field(min_length=20, max_length=5000)


class AppealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appeal_id: str
    case_id: str
    original_decision_id: int
    submitted_by_learner_id: int
    appeal_reason: str
    appeal_status: str
    submitted_at: datetime
    due_at: Optional[datetime] = None
    outcome: Optional[str] = None
    resolved_at: Optional[datetime] = None