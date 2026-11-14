from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.evidence_write import EvidenceCreateRequest
from app.services import evidence_write_service
from app.api.v1 import case_evidence

router = APIRouter(tags=["Case Evidence"])


@router.post("/cases/{case_id}/evidence", status_code=201)
def add_case_evidence(
    case_id: str,
    payload: EvidenceCreateRequest,
    db: Session = Depends(get_db),
):
    return evidence_write_service.create_evidence(
        db=db,
        case_id=case_id,
        evidence_type=payload.evidence_type,
        evidence_reference=payload.evidence_reference,
        description=payload.description,
        content_hash=payload.content_hash,
        added_by=payload.added_by,
    )
