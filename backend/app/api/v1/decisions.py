from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.decision import (
    DecisionCreateRequest,
    DecisionListResponse,
    DecisionResponse,
)

from app.services.decision_service import (
    list_decisions,
    get_decision_detail,
    create_decision,
)

router = APIRouter(
    prefix="/decisions",
    tags=["Decisions"],
)


@router.get("", response_model=DecisionListResponse)
def get_decisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_id: str | None = None,
    reviewer_id: int | None = Query(None, ge=1),
    decision_type: str | None = None,
    decision_stage: str | None = None,
    db: Session = Depends(get_db),
):
    allowed_types = {
        "NO_VIOLATION",
        "ACADEMIC_MISCONDUCT",
        "INSUFFICIENT_EVIDENCE",
        "REQUEST_MORE_EVIDENCE",
        "UPHELD",
        "OVERTURNED",
        "MODIFIED",
    }

    if decision_type and decision_type not in allowed_types:
        raise HTTPException(
            400,
            "Invalid decision_type",
        )

    if decision_stage and decision_stage not in {
        "INITIAL",
        "REASSESSMENT",
    }:
        raise HTTPException(
            400,
            "Invalid decision_stage",
        )

    total, decisions = list_decisions(
        db=db,
        page=page,
        page_size=page_size,
        case_id=case_id,
        reviewer_id=reviewer_id,
        decision_type=decision_type,
        decision_stage=decision_stage,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "decisions": decisions,
    }


@router.get("/{decision_id}", response_model=DecisionResponse)
def get_decision(
    decision_id: int,
    db: Session = Depends(get_db),
):
    decision = get_decision_detail(db, decision_id)

    if decision is None:
        raise HTTPException(
            404,
            "Decision not found",
        )

    return decision


@router.post("", status_code=201)
def submit_decision(
    case_id: str,
    payload: DecisionCreateRequest,
    db: Session = Depends(get_db),
):
    return create_decision(
        db=db,
        case_id=case_id,
        reviewer_id=payload.reviewer_id,
        decision_type=payload.decision_type,
        rationale=payload.rationale,
    )