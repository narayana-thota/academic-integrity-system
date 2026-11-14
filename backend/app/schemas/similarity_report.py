
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReportMatchResponse(BaseModel):
    match_id: int
    match_sequence: int
    source_reference: str
    match_percentage: float
    match_type: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SimilarityReportResponse(BaseModel):
    report_id: str
    submission_id: str
    evaluated_rule_id: Optional[str] = None
    similarity_score: float
    matched_source_count: int
    report_category: str
    review_action: str
    generated_at: datetime
    generator_version: str

    model_config = ConfigDict(from_attributes=True)


class SimilarityReportDetailResponse(SimilarityReportResponse):
    matches: list[ReportMatchResponse]
    case_id: Optional[str] = None
    case_status: Optional[str] = None


class SimilarityReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    reports: list[SimilarityReportResponse]
