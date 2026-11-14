
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CaseListItem(BaseModel):
    case_id: str
    submission_id: str
    report_id: str
    case_status: str
    priority: str
    created_at: datetime
    due_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    learner_code: str
    learner_name: str
    similarity_score: float
    review_action: str


class CaseListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    cases: list[CaseListItem]


class CaseEventResponse(BaseModel):
    event_id: int
    event_type: str
    event_description: str
    actor_reference: str
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseEvidenceResponse(BaseModel):
    evidence_id: str
    evidence_type: str
    description: str
    version: int
    added_by: str
    created_at: datetime


class CaseAssignmentResponse(BaseModel):
    assignment_id: int
    reviewer_id: int
    reviewer_name: str
    assignment_status: str
    assigned_at: datetime
    ended_at: Optional[datetime] = None


class CaseDecisionResponse(BaseModel):
    decision_id: int
    reviewer_id: int
    decision_type: str
    decision_stage: str
    rationale: str
    decided_at: datetime


class CaseAppealResponse(BaseModel):
    appeal_id: str
    appeal_status: str
    appeal_reason: str
    outcome: Optional[str] = None
    submitted_at: datetime
    resolved_at: Optional[datetime] = None


class CaseDetailResponse(CaseListItem):
    rule_id: str
    closure_reason: Optional[str] = None
    events: list[CaseEventResponse]
    evidence: list[CaseEvidenceResponse]
    assignments: list[CaseAssignmentResponse]
    decisions: list[CaseDecisionResponse]
    appeals: list[CaseAppealResponse]
