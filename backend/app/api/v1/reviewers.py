
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.reviewer_service import (
    list_reviewers,
    list_assignments,
    check_reviewer_eligibility,
)
from app.schemas.assignment import AssignmentCreateRequest

from app.services.reviewer_service import (
    create_reviewer_assignment,
)

router = APIRouter(tags=["Reviewers and Assignments"])


@router.get("/reviewers")
def get_reviewers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    total, reviewers = list_reviewers(
        db, page, page_size, active_only
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "reviewers": reviewers,
    }


@router.get("/reviewer-assignments")
def get_reviewer_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reviewer_id: int | None = Query(None, ge=1),
    case_id: str | None = None,
    assignment_status: str | None = None,
    db: Session = Depends(get_db),
):
    allowed_statuses = {"ACTIVE", "COMPLETED", "REVOKED"}

    if assignment_status and assignment_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid assignment_status"
        )

    total, rows = list_assignments(
        db=db,
        page=page,
        page_size=page_size,
        reviewer_id=reviewer_id,
        case_id=case_id,
        assignment_status=assignment_status,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "assignments": [
            {
                "assignment_id": assignment.assignment_id,
                "case_id": assignment.case_id,
                "reviewer_id": assignment.reviewer_id,
                "reviewer_name": reviewer.full_name,
                "assignment_status": assignment.assignment_status,
                "assigned_at": assignment.assigned_at,
                "ended_at": assignment.ended_at,
                "assigned_by": assignment.assigned_by,
                "end_reason": assignment.end_reason,
            }
            for assignment, reviewer in rows
        ],
    }


@router.get("/cases/{case_id}/reviewer-eligibility/{reviewer_id}")
def get_reviewer_eligibility(
    case_id: str,
    reviewer_id: int,
    db: Session = Depends(get_db),
):
    case, reviewer, result = check_reviewer_eligibility(
        db, case_id, reviewer_id
    )

    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    if reviewer is None:
        raise HTTPException(status_code=404, detail="Reviewer not found")

    return {
        "case_id": case_id,
        "reviewer_id": reviewer_id,
        **result,
    }


@router.post(
    "/cases/{case_id}/assignments",
    status_code=201
)
def create_assignment(
    case_id: str,
    payload: AssignmentCreateRequest,
    db: Session = Depends(get_db),
):
    return create_reviewer_assignment(
        db=db,
        case_id=case_id,
        reviewer_id=payload.reviewer_id,
        assigned_by=payload.assigned_by,
    )
