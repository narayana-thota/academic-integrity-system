from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import history_service

router = APIRouter(tags=["Case Timeline and Audit"])


@router.get("/cases/{case_id}/timeline")
def get_case_timeline(
    case_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return history_service.get_case_timeline(
        db, case_id, page, page_size
    )


@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    case_id: str | None = None,
    entity_type: str | None = None,
    entity_reference: str | None = None,
    actor_reference: str | None = None,
    action: str | None = None,
    db: Session = Depends(get_db),
):
    return history_service.list_audit_logs(
        db,
        page,
        page_size,
        case_id,
        entity_type,
        entity_reference,
        actor_reference,
        action,
    )


@router.get("/audit-logs/{audit_id}")
def get_audit_log(
    audit_id: int,
    db: Session = Depends(get_db),
):
    return history_service.get_audit_log(db, audit_id)
