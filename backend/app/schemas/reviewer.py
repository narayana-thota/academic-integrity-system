
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReviewerResponse(BaseModel):
    reviewer_id: int
    reviewer_code: str
    full_name: str
    email: str
    role: str
    department: str
    max_active_cases: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ReviewerListResponse(BaseModel):
    total: int
    reviewers: list[ReviewerResponse]


class AssignmentResponse(BaseModel):
    assignment_id: int
    case_id: str
    reviewer_id: int
    reviewer_name: str
    assignment_status: str
    assigned_at: datetime
    ended_at: Optional[datetime] = None
    assigned_by: str
    end_reason: Optional[str] = None


class AssignmentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    assignments: list[AssignmentResponse]


class ReviewerEligibilityResponse(BaseModel):
    case_id: str
    reviewer_id: int
    eligible: bool
    reasons: list[str]
    current_active_cases: int
    maximum_active_cases: int
