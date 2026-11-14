from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func

from app.database import Base


def get_models():
    return {
        "Case": Base.classes.cases,
        "Evidence": Base.classes.evidence_items,
        "CaseEvidence": Base.classes.case_evidence,
        "Event": Base.classes.case_events,
        "Audit": Base.classes.audit_logs,
    }


def add_history(db, case_id, actor, evidence_id, action, description, data):
    models = get_models()
    now = datetime.utcnow()

    db.add(models["Event"](
        case_id=case_id,
        event_type=action,
        event_description=description,
        actor_reference=str(actor),
        event_data=data,
        occurred_at=now,
    ))

    db.add(models["Audit"](
        case_id=case_id,
        actor_type="USER",
        actor_reference=str(actor),
        entity_type="EVIDENCE",
        entity_reference=evidence_id,
        action=action,
        event_data=data,
        created_at=now,
    ))


def create_evidence(
    db,
    case_id,
    evidence_type,
    evidence_reference,
    description,
    content_hash,
    added_by,
):
    models = get_models()
    Case = models["Case"]
    Evidence = models["Evidence"]
    CaseEvidence = models["CaseEvidence"]

    evidence_reference = evidence_reference.strip()
    description = description.strip()
    added_by = added_by.strip()

    with db.begin():
        case = (
            db.query(Case)
            .filter(Case.case_id == case_id)
            .with_for_update()
            .first()
        )

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.case_status in ("CLOSED", "APPEALED", "APPEAL_REVIEW"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Evidence cannot be added through this endpoint while the "
                    "case is closed or undergoing appeal. Use the formal "
                    "reopening or appeal process."
                ),
            )

        latest_version = (
            db.query(func.max(Evidence.version))
            .filter(
                Evidence.evidence_type == evidence_type,
                Evidence.evidence_reference == evidence_reference,
            )
            .scalar()
        )

        next_version = (latest_version or 0) + 1

        linked_count = (
            db.query(func.count(CaseEvidence.case_evidence_id))
            .filter(CaseEvidence.case_id == case_id)
            .scalar()
            or 0
        )

        evidence_id = f"EVD-{case_id}-{linked_count + 1:03d}"

        # Defensive check: never overwrite an existing evidence record.
        if db.query(Evidence).filter(
            Evidence.evidence_id == evidence_id
        ).first():
            raise HTTPException(
                status_code=409,
                detail="Evidence identifier already exists; no record was changed",
            )

        now = datetime.utcnow()
        previous_status = case.case_status

        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            evidence_reference=evidence_reference,
            description=description,
            content_hash=content_hash,
            version=next_version,
            added_by=added_by,
            created_at=now,
        )
        db.add(evidence)
        db.flush()

        link = CaseEvidence(
            case_id=case_id,
            evidence_id=evidence_id,
            linked_at=now,
        )
        db.add(link)

        # A decided case is reopened for a fresh human review.
        # Existing decisions and their rationale are never modified.
        if previous_status == "DECIDED":
            case.case_status = "OPEN"

        add_history(
            db,
            case_id,
            added_by,
            evidence_id,
            "EVIDENCE_ADDED",
            "New evidence version added to the case",
            {
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
                "version": next_version,
                "previous_case_status": previous_status,
                "new_case_status": case.case_status,
                "previous_decisions_preserved": True,
            },
        )

        db.flush()

    return {
        "evidence_id": evidence_id,
        "case_id": case_id,
        "evidence_type": evidence_type,
        "evidence_reference": evidence_reference,
        "version": next_version,
        "added_by": added_by,
        "created_at": now,
        "case_status": case.case_status,
        "message": "Evidence added successfully. Existing evidence and decisions were preserved.",
    }
