
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.evidence_service import (
    list_evidence,
    get_evidence_by_id,
    get_evidence_cases,
)

from app.schemas.evidence import (
    EvidenceResponse,
    EvidenceListResponse,
)

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)


@router.get("", response_model=EvidenceListResponse)
def get_evidence_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_id: str | None = None,
    evidence_type: str | None = None,
    db: Session = Depends(get_db),
):
    allowed_types = {
        "CODE_MATCH",
        "TEXT_MATCH",
        "DOCUMENT",
        "STATEMENT",
        "OTHER",
    }

    if evidence_type and evidence_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid evidence_type"
        )

    total, records = list_evidence(
        db=db,
        page=page,
        page_size=page_size,
        case_id=case_id,
        evidence_type=evidence_type,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "evidence": records,
    }


@router.get("/{evidence_id}")
def get_evidence_detail(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    evidence = get_evidence_by_id(db, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    case_links = get_evidence_cases(db, evidence_id)

    return {
        "evidence_id": evidence.evidence_id,
        "evidence_type": evidence.evidence_type,
        "evidence_reference": evidence.evidence_reference,
        "description": evidence.description,
        "content_hash": evidence.content_hash,
        "version": evidence.version,
        "added_by": evidence.added_by,
        "created_at": evidence.created_at,
        "linked_cases": [
            {
                "case_id": link.case_id,
                "linked_at": link.linked_at,
            }
            for link in case_links
        ],
    }
