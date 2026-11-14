
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.case_service import (
    list_cases,
    get_case_detail,
)

from app.schemas.case import (
    CaseListResponse,
    CaseDetailResponse,
)

router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


@router.get("", response_model=CaseListResponse)
def get_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_status: str | None = None,
    priority: str | None = None,
    learner_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "OPEN", "ASSIGNED", "UNDER_REVIEW",
        "DECIDED", "APPEALED", "APPEAL_REVIEW",
        "CLOSED",
    }

    allowed_priorities = {
        "LOW", "MEDIUM", "HIGH", "CRITICAL"
    }

    if case_status and case_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid case_status"
        )

    if priority and priority not in allowed_priorities:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority"
        )

    total, cases = list_cases(
        db=db,
        page=page,
        page_size=page_size,
        case_status=case_status,
        priority=priority,
        learner_id=learner_id,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "cases": cases,
    }


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
):
    case = get_case_detail(db, case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case
