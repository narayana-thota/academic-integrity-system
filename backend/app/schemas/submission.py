
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LearnerSummary(BaseModel):
    learner_id: int
    learner_code: str
    full_name: str
    department: str

    model_config = ConfigDict(from_attributes=True)


class AssessmentSummary(BaseModel):
    assessment_id: int
    assessment_code: str
    title: str
    assessment_type: str

    model_config = ConfigDict(from_attributes=True)


class SimilarityReportSummary(BaseModel):
    report_id: str
    similarity_score: float
    matched_source_count: int
    report_category: str
    review_action: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionResponse(BaseModel):
    submission_id: str
    submitted_at: datetime
    attempt_number: int
    status: str

    learner: LearnerSummary
    assessment: AssessmentSummary
    similarity_reports: list[SimilarityReportSummary]

    model_config = ConfigDict(from_attributes=True)


class SubmissionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    submissions: list[SubmissionResponse]
