
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.similarity_report_service import (
    list_reports,
    get_report_by_id,
    get_report_matches,
    get_case_for_report,
)

from app.schemas.similarity_report import (
    SimilarityReportResponse,
    SimilarityReportDetailResponse,
    SimilarityReportListResponse,
)

router = APIRouter(
    prefix="/similarity-reports",
    tags=["Similarity Reports"]
)


@router.get("", response_model=SimilarityReportListResponse)
def get_similarity_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    review_action: str | None = None,
    report_category: str | None = None,
    db: Session = Depends(get_db),
):
    if review_action and review_action not in {
        "NO_FLAG", "MONITOR", "REVIEW"
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid review_action"
        )

    if report_category and report_category not in {
        "LOW", "MODERATE", "HIGH", "CRITICAL"
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid report_category"
        )

    total, reports = list_reports(
        db=db,
        page=page,
        page_size=page_size,
        review_action=review_action,
        report_category=report_category,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "reports": reports,
    }


@router.get(
    "/{report_id}",
    response_model=SimilarityReportDetailResponse
)
def get_similarity_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    report = get_report_by_id(db, report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Similarity report not found"
        )

    matches = get_report_matches(db, report_id)
    case = get_case_for_report(db, report_id)

    return {
        "report_id": report.report_id,
        "submission_id": report.submission_id,
        "evaluated_rule_id": report.evaluated_rule_id,
        "similarity_score": float(report.similarity_score),
        "matched_source_count": report.matched_source_count,
        "report_category": report.report_category,
        "review_action": report.review_action,
        "generated_at": report.generated_at,
        "generator_version": report.generator_version,
        "matches": [
            {
                "match_id": match.match_id,
                "match_sequence": match.match_sequence,
                "source_reference": match.source_reference,
                "match_percentage": float(match.match_percentage),
                "match_type": match.match_type,
                "description": match.description,
            }
            for match in matches
        ],
        "case_id": case.case_id if case else None,
        "case_status": case.case_status if case else None,
    }
