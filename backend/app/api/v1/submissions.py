
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.submission_service import (
    list_submissions,
    get_submission_by_id,
    get_submission_models,
)
from app.schemas.submission import (
    SubmissionResponse,
    SubmissionListResponse,
)

router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"]
)


def serialize_submission(submission):
    Submission, Learner, Assessment, Report = get_submission_models()

    learner = (
        # Retrieve related records explicitly to avoid relying
        # on automatically generated ORM relationships.
        None
    )

    return submission


def build_submission_response(db, submission):
    Submission, Learner, Assessment, Report = get_submission_models()

    learner = db.query(Learner).filter(
        Learner.learner_id == submission.learner_id
    ).one()

    assessment = db.query(Assessment).filter(
        Assessment.assessment_id == submission.assessment_id
    ).one()

    reports = db.query(Report).filter(
        Report.submission_id == submission.submission_id
    ).order_by(Report.generated_at.desc()).all()

    return {
        "submission_id": submission.submission_id,
        "submitted_at": submission.submitted_at,
        "attempt_number": submission.attempt_number,
        "status": submission.status,
        "learner": {
            "learner_id": learner.learner_id,
            "learner_code": learner.learner_code,
            "full_name": learner.full_name,
            "department": learner.department,
        },
        "assessment": {
            "assessment_id": assessment.assessment_id,
            "assessment_code": assessment.assessment_code,
            "title": assessment.title,
            "assessment_type": assessment.assessment_type,
        },
        "similarity_reports": [
            {
                "report_id": report.report_id,
                "similarity_score": float(report.similarity_score),
                "matched_source_count": report.matched_source_count,
                "report_category": report.report_category,
                "review_action": report.review_action,
                "generated_at": report.generated_at,
            }
            for report in reports
        ],
    }


@router.get("", response_model=SubmissionListResponse)
def get_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    learner_id: int | None = None,
    assessment_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    total, submissions = list_submissions(
        db=db,
        page=page,
        page_size=page_size,
        learner_id=learner_id,
        assessment_id=assessment_id,
        status=status,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "submissions": [
            build_submission_response(db, submission)
            for submission in submissions
        ],
    }


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
):
    submission = get_submission_by_id(db, submission_id)

    if submission is None:
        raise HTTPException(
            status_code=404,
            detail="Submission not found"
        )

    return build_submission_response(db, submission)
