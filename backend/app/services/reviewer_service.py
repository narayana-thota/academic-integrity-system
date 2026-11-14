from app.database import Base

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func


def get_reviewer_models():
    return {
        "Reviewer": Base.classes.reviewers,
        "Assignment": Base.classes.reviewer_assignments,
        "Case": Base.classes.cases,
        "Submission": Base.classes.submissions,
        "Conflict": Base.classes.reviewer_conflicts,
    }


def list_reviewers(db, page=1, page_size=20, active_only=True):
    m = get_reviewer_models()
    Reviewer = m["Reviewer"]

    query = db.query(Reviewer)

    if active_only:
        query = query.filter(Reviewer.is_active.is_(True))

    total = query.count()

    records = (
        query.order_by(Reviewer.reviewer_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, records


def list_assignments(
    db,
    page=1,
    page_size=20,
    reviewer_id=None,
    case_id=None,
    assignment_status=None,
):
    m = get_reviewer_models()
    Assignment = m["Assignment"]
    Reviewer = m["Reviewer"]

    query = db.query(Assignment, Reviewer).join(
        Reviewer,
        Assignment.reviewer_id == Reviewer.reviewer_id
    )

    if reviewer_id is not None:
        query = query.filter(Assignment.reviewer_id == reviewer_id)

    if case_id:
        query = query.filter(Assignment.case_id == case_id)

    if assignment_status:
        query = query.filter(
            Assignment.assignment_status == assignment_status
        )

    total = query.count()

    rows = (
        query.order_by(
            Assignment.assigned_at.desc(),
            Assignment.assignment_id.desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, rows


def check_reviewer_eligibility(db, case_id, reviewer_id):
    m = get_reviewer_models()

    Reviewer = m["Reviewer"]
    Assignment = m["Assignment"]
    Case = m["Case"]
    Submission = m["Submission"]
    Conflict = m["Conflict"]

    reasons = []

    case = db.query(Case).filter(
        Case.case_id == case_id
    ).one_or_none()

    reviewer = db.query(Reviewer).filter(
        Reviewer.reviewer_id == reviewer_id
    ).one_or_none()

    if case is None:
        return None, None, {
            "eligible": False,
            "reasons": ["Case not found"],
            "current_active_cases": 0,
            "maximum_active_cases": 0,
        }

    if reviewer is None:
        return case, None, {
            "eligible": False,
            "reasons": ["Reviewer not found"],
            "current_active_cases": 0,
            "maximum_active_cases": 0,
        }

    if case.case_status == "CLOSED":
        reasons.append("Closed cases cannot receive new assignments")

    if case.case_status not in {"OPEN", "ASSIGNED"}:
        reasons.append(
            f"Case status {case.case_status} does not allow assignment"
        )

    if not reviewer.is_active:
        reasons.append("Reviewer is inactive")

    submission = db.query(Submission).filter(
        Submission.submission_id == case.submission_id
    ).one()

    conflicts = db.query(Conflict).filter(
        Conflict.reviewer_id == reviewer_id,
        Conflict.is_active.is_(True),
    ).all()

    for conflict in conflicts:
        if (
            conflict.learner_id == submission.learner_id
            or conflict.assessment_id == submission.assessment_id
        ):
            reasons.append(
                f"Active conflict of interest: {conflict.conflict_type}"
            )

    current_load = db.query(Assignment).filter(
        Assignment.reviewer_id == reviewer_id,
        Assignment.assignment_status == "ACTIVE",
    ).count()

    if current_load >= reviewer.max_active_cases:
        reasons.append("Reviewer has reached maximum active case capacity")

    existing_assignment = db.query(Assignment).filter(
        Assignment.case_id == case_id,
        Assignment.assignment_status == "ACTIVE",
    ).first()

    if existing_assignment:
        reasons.append("Case already has an active reviewer assignment")

    result = {
        "eligible": len(reasons) == 0,
        "reasons": reasons,
        "current_active_cases": current_load,
        "maximum_active_cases": reviewer.max_active_cases,
    }

    return case, reviewer, result

def create_reviewer_assignment(
    db,
    case_id: str,
    reviewer_id: int,
    assigned_by: str,
):
    m = get_reviewer_models()

    Case = m["Case"]
    Reviewer = m["Reviewer"]
    Assignment = m["Assignment"]
    Submission = m["Submission"]
    Conflict = m["Conflict"]

    Event = Base.classes.case_events
    Audit = Base.classes.audit_logs

    try:
        with db.begin():

            # Lock the case and reviewer rows to prevent
            # concurrent assignment operations.
            case = (
                db.query(Case)
                .filter(Case.case_id == case_id)
                .with_for_update()
                .one_or_none()
            )

            if case is None:
                raise HTTPException(404, "Case not found")

            reviewer = (
                db.query(Reviewer)
                .filter(Reviewer.reviewer_id == reviewer_id)
                .with_for_update()
                .one_or_none()
            )

            if reviewer is None:
                raise HTTPException(404, "Reviewer not found")

            # Only open cases can receive a new assignment.
            if case.case_status != "OPEN":
                raise HTTPException(
                    409,
                    f"Case cannot be assigned from status {case.case_status}"
                )

            if not reviewer.is_active:
                raise HTTPException(
                    409,
                    "Reviewer is inactive"
                )

            submission = db.query(Submission).filter(
                Submission.submission_id == case.submission_id
            ).one()

            # Check active conflicts against both learner
            # and assessment.
            conflicts = db.query(Conflict).filter(
                Conflict.reviewer_id == reviewer_id,
                Conflict.is_active.is_(True),
            ).all()

            for conflict in conflicts:
                if (
                    conflict.learner_id == submission.learner_id
                    or conflict.assessment_id == submission.assessment_id
                ):
                    raise HTTPException(
                        409,
                        "Reviewer has an active conflict of interest"
                    )

            # Check current reviewer workload.
            active_load = (
                db.query(func.count(Assignment.assignment_id))
                .filter(
                    Assignment.reviewer_id == reviewer_id,
                    Assignment.assignment_status == "ACTIVE",
                )
                .scalar()
            )

            if active_load >= reviewer.max_active_cases:
                raise HTTPException(
                    409,
                    "Reviewer has reached maximum active case capacity"
                )

            # Prevent another active assignment for this case.
            existing = db.query(Assignment).filter(
                Assignment.case_id == case_id,
                Assignment.assignment_status == "ACTIVE",
            ).first()

            if existing:
                raise HTTPException(
                    409,
                    "Case already has an active reviewer assignment"
                )

            now = datetime.now(timezone.utc).replace(tzinfo=None)

            assignment = Assignment(
                case_id=case_id,
                reviewer_id=reviewer_id,
                assignment_status="ACTIVE",
                assigned_at=now,
                assigned_by=assigned_by,
            )

            db.add(assignment)
            db.flush()

            old_status = case.case_status
            case.case_status = "ASSIGNED"

            event_data = {
                "assignment_id": assignment.assignment_id,
                "reviewer_id": reviewer_id,
                "previous_status": old_status,
                "new_status": "ASSIGNED",
            }

            # Append-only case event.
            db.add(Event(
                case_id=case_id,
                event_type="REVIEWER_ASSIGNED",
                event_description=(
                    f"Reviewer {reviewer_id} assigned to case {case_id}"
                ),
                actor_reference=assigned_by,
                event_data=event_data,
                occurred_at=now,
            ))

            # Record status transition separately.
            db.add(Event(
                case_id=case_id,
                event_type="CASE_STATUS_CHANGED",
                event_description=(
                    f"Case status changed from {old_status} to ASSIGNED"
                ),
                actor_reference=assigned_by,
                event_data=event_data,
                occurred_at=now,
            ))

            # Audit record for reviewer assignment.
            db.add(Audit(
                case_id=case_id,
                actor_type="SYSTEM_USER",
                actor_reference=assigned_by,
                entity_type="REVIEWER_ASSIGNMENT",
                entity_reference=str(assignment.assignment_id),
                action="CREATE",
                event_data=event_data,
                created_at=now,
            ))

            # Audit record for case status change.
            db.add(Audit(
                case_id=case_id,
                actor_type="SYSTEM_USER",
                actor_reference=assigned_by,
                entity_type="CASE",
                entity_reference=case_id,
                action="STATUS_CHANGE",
                event_data=event_data,
                created_at=now,
            ))

            db.flush()

            result = {
                "assignment_id": assignment.assignment_id,
                "case_id": case_id,
                "reviewer_id": reviewer_id,
                "reviewer_name": reviewer.full_name,
                "assignment_status": assignment.assignment_status,
                "assigned_at": assignment.assigned_at,
                "assigned_by": assignment.assigned_by,
                "case_status": case.case_status,
            }

        return result

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise
