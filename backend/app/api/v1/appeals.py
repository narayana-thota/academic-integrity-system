from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.appeal import (
    AppealCreateRequest,
    AppealResolveRequest,
)
from app.services import appeal_service

router = APIRouter(prefix="/appeals", tags=["Appeals"])


@router.get("")
def get_appeals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_id: str | None = None,
    status: str | None = None,
    learner_id: int | None = None,
    db: Session = Depends(get_db),
):
    return appeal_service.list_appeals(
        db, page, page_size, case_id, status, learner_id
    )


@router.get("/{appeal_id}")
def get_appeal(
    appeal_id: str,
    db: Session = Depends(get_db),
):
    return appeal_service.get_appeal(db, appeal_id)


@router.post("/cases/{case_id}", status_code=201)
def submit_appeal(
    case_id: str,
    payload: AppealCreateRequest,
    db: Session = Depends(get_db),
):
    return appeal_service.create_appeal(
        db,
        case_id,
        payload.learner_id,
        payload.appeal_reason,
    )


@router.post("/{appeal_id}/resolve")
def resolve_appeal(
    appeal_id: str,
    payload: AppealResolveRequest,
    db: Session = Depends(get_db),
):
    return appeal_service.resolve_appeal(
        db,
        appeal_id,
        payload.reviewer_id,
        payload.outcome,
        payload.rationale,
    )
