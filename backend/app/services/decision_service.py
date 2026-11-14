from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import desc

from app.database import Base


ALLOWED_DECISION_TYPES = {
    "NO_VIOLATION",
    "ACADEMIC_MISCONDUCT",
    "INSUFFICIENT_EVIDENCE",
    "REQUEST_MORE_EVIDENCE",
}


def get_decision_models():
    return {
        "Decision": Base.classes.decisions,
        "Case": Base.classes.cases,
        "Assignment": Base.classes.reviewer_assignments,
        "Reviewer": Base.classes.reviewers,
        "Event": Base.classes.case_events,
        "Audit": Base.classes.audit_logs,
    }


def list_decisions(
    db,
    page=1,
    page_size=20,
    case_id=None,
    reviewer_id=None,
    decision_type=None,
    decision_stage=None,
):
    m = get_decision_models()

    Decision = m["Decision"]
    Reviewer = m["Reviewer"]

    query = db.query(Decision, Reviewer).join(
        Reviewer,
        Decision.reviewer_id == Reviewer.reviewer_id,
    )

    if case_id:
        query = query.filter(Decision.case_id == case_id)

    if reviewer_id is not None:
        query = query.filter(Decision.reviewer_id == reviewer_id)

    if decision_type:
        query = query.filter(
            Decision.decision_type == decision_type
        )

    if decision_stage:
        query = query.filter(
            Decision.decision_stage == decision_stage
        )

    total = query.count()

    rows = (
        query.order_by(
            desc(Decision.decided_at),
            desc(Decision.decision_id),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []

    for decision, reviewer in rows:
        results.append({
            "decision_id": decision.decision_id,
            "case_id": decision.case_id,
            "reviewer_id": decision.reviewer_id,
            "reviewer_name": reviewer.full_name,
            "decision_type": decision.decision_type,
            "decision_stage": decision.decision_stage,
            "rationale": decision.rationale,
            "decided_at": decision.decided_at,
            "supersedes_decision_id": (
                decision.supersedes_decision_id
            ),
        })

    return total, results


def get_decision_detail(db, decision_id):
    m = get_decision_models()

    Decision = m["Decision"]
    Reviewer = m["Reviewer"]

    row = (
        db.query(Decision, Reviewer)
        .join(
            Reviewer,
            Decision.reviewer_id == Reviewer.reviewer_id,
        )
        .filter(Decision.decision_id == decision_id)
        .one_or_none()
    )

    if row is None:
        return None

    decision, reviewer = row

    return {
        "decision_id": decision.decision_id,
        "case_id": decision.case_id,
        "reviewer_id": decision.reviewer_id,
        "reviewer_name": reviewer.full_name,
        "decision_type": decision.decision_type,
        "decision_stage": decision.decision_stage,
        "rationale": decision.rationale,
        "decided_at": decision.decided_at,
        "supersedes_decision_id": (
            decision.supersedes_decision_id
        ),
    }


def create_decision(
    db,
    case_id,
    reviewer_id,
    decision_type,
    rationale,
):
    if decision_type not in ALLOWED_DECISION_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid decision_type",
        )

    m = get_decision_models()

    Decision = m["Decision"]
    Case = m["Case"]
    Assignment = m["Assignment"]
    Reviewer = m["Reviewer"]
    Event = m["Event"]
    Audit = m["Audit"]

    try:
        with db.begin():

            # Lock the case to prevent concurrent decisions.
            case = (
                db.query(Case)
                .filter(Case.case_id == case_id)
                .with_for_update()
                .one_or_none()
            )

            if case is None:
                raise HTTPException(404, "Case not found")

            if case.case_status not in {
                "ASSIGNED",
                "UNDER_REVIEW",
            }:
                raise HTTPException(
                    409,
                    f"Case cannot receive a decision in status "
                    f"{case.case_status}",
                )

            reviewer = (
                db.query(Reviewer)
                .filter(
                    Reviewer.reviewer_id == reviewer_id
                )
                .one_or_none()
            )

            if reviewer is None:
                raise HTTPException(
                    404,
                    "Reviewer not found",
                )

            if not reviewer.is_active:
                raise HTTPException(
                    409,
                    "Reviewer is inactive",
                )

            # The decision must come from the active
            # reviewer assigned to this case.
            assignment = (
                db.query(Assignment)
                .filter(
                    Assignment.case_id == case_id,
                    Assignment.reviewer_id == reviewer_id,
                    Assignment.assignment_status == "ACTIVE",
                )
                .with_for_update()
                .one_or_none()
            )

            if assignment is None:
                raise HTTPException(
                    403,
                    "Reviewer has no active assignment for this case",
                )

            # Preserve decision history. A follow-up decision
            # is allowed only after REQUEST_MORE_EVIDENCE.
            previous = (
                db.query(Decision)
                .filter(
                    Decision.case_id == case_id,
                    Decision.decision_stage == "INITIAL",
                )
                .order_by(
                    Decision.decided_at.desc(),
                    Decision.decision_id.desc(),
                )
                .with_for_update()
                .first()
            )

            if previous and (
                previous.decision_type != "REQUEST_MORE_EVIDENCE"
            ):
                raise HTTPException(
                    409,
                    "An initial decision already exists for this case",
                )

            now = datetime.now(timezone.utc).replace(
                tzinfo=None
            )

            decision = Decision(
                case_id=case_id,
                reviewer_id=reviewer_id,
                decision_type=decision_type,
                decision_stage="INITIAL",
                rationale=rationale.strip(),
                decided_at=now,
                supersedes_decision_id=(
                    previous.decision_id if previous else None
                ),
            )

            db.add(decision)
            db.flush()

            old_status = case.case_status

            if decision_type == "REQUEST_MORE_EVIDENCE":
                case.case_status = "UNDER_REVIEW"
                # Keep the assignment ACTIVE so the reviewer
                # can continue reviewing the case.
            else:
                case.case_status = "DECIDED"
                assignment.assignment_status = "COMPLETED"
                assignment.ended_at = now
                assignment.end_reason = (
                    "Initial decision submitted"
                )

            event_data = {
                "decision_id": decision.decision_id,
                "reviewer_id": reviewer_id,
                "decision_type": decision_type,
                "decision_stage": "INITIAL",
                "previous_status": old_status,
                "new_status": case.case_status,
                "supersedes_decision_id": (
                    decision.supersedes_decision_id
                ),
            }

            db.add(Event(
                case_id=case_id,
                event_type="DECISION_RECORDED",
                event_description=(
                    f"{decision_type} recorded for case {case_id}"
                ),
                actor_reference=str(reviewer_id),
                event_data=event_data,
                occurred_at=now,
            ))

            if old_status != case.case_status:
                db.add(Event(
                    case_id=case_id,
                    event_type="CASE_STATUS_CHANGED",
                    event_description=(
                        f"Case status changed from {old_status} "
                        f"to {case.case_status}"
                    ),
                    actor_reference=str(reviewer_id),
                    event_data=event_data,
                    occurred_at=now,
                ))

            db.add(Audit(
                case_id=case_id,
                actor_type="REVIEWER",
                actor_reference=str(reviewer_id),
                entity_type="DECISION",
                entity_reference=str(decision.decision_id),
                action="CREATE",
                event_data=event_data,
                created_at=now,
            ))

            db.add(Audit(
                case_id=case_id,
                actor_type="REVIEWER",
                actor_reference=str(reviewer_id),
                entity_type="CASE",
                entity_reference=case_id,
                action="STATUS_CHANGE",
                event_data=event_data,
                created_at=now,
            ))

            db.flush()

            result = {
                "decision_id": decision.decision_id,
                "case_id": case_id,
                "reviewer_id": reviewer_id,
                "reviewer_name": reviewer.full_name,
                "decision_type": decision.decision_type,
                "decision_stage": decision.decision_stage,
                "rationale": decision.rationale,
                "decided_at": decision.decided_at,
                "supersedes_decision_id": (
                    decision.supersedes_decision_id
                ),
                "case_status": case.case_status,
            }

        return result

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise