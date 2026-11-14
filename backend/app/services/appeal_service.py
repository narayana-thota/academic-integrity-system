from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import func

from app.database import Base


def get_models():
    return {
        "Case": Base.classes.cases,
        "Submission": Base.classes.submissions,
        "Reviewer": Base.classes.reviewers,
        "Conflict": Base.classes.reviewer_conflicts,
        "Decision": Base.classes.decisions,
        "Appeal": Base.classes.appeals,
        "AppealReview": Base.classes.appeal_reviews,
        "Event": Base.classes.case_events,
        "Audit": Base.classes.audit_logs,
    }


def add_history(db, case_id, actor_type, actor_reference,
                entity_type, entity_reference, action, description,
                event_data=None):
    models = get_models()
    now = datetime.utcnow()

    db.add(models["Event"](
        case_id=case_id,
        event_type=action,
        event_description=description,
        actor_reference=str(actor_reference),
        event_data=event_data or {},
        occurred_at=now,
    ))

    db.add(models["Audit"](
        case_id=case_id,
        actor_type=actor_type,
        actor_reference=str(actor_reference),
        entity_type=entity_type,
        entity_reference=str(entity_reference),
        action=action,
        event_data=event_data or {},
        created_at=now,
    ))


def list_appeals(db, page=1, page_size=20, case_id=None,
                 status=None, learner_id=None):
    models = get_models()
    Appeal = models["Appeal"]

    query = db.query(Appeal)

    if case_id:
        query = query.filter(Appeal.case_id == case_id)

    if status:
        query = query.filter(Appeal.appeal_status == status)

    if learner_id:
        query = query.filter(
            Appeal.submitted_by_learner_id == learner_id
        )

    total = query.count()
    rows = (
        query.order_by(Appeal.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_appeal(db, appeal_id):
    models = get_models()
    Appeal = models["Appeal"]

    appeal = db.query(Appeal).filter(
        Appeal.appeal_id == appeal_id
    ).first()

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    reviews = (
        db.query(models["AppealReview"])
        .filter(models["AppealReview"].appeal_id == appeal_id)
        .order_by(models["AppealReview"].reviewed_at.asc())
        .all()
    )

    return {
        "appeal": appeal,
        "reviews": reviews,
    }


def create_appeal(db, case_id, learner_id, appeal_reason):
    models = get_models()
    Case = models["Case"]
    Submission = models["Submission"]
    Decision = models["Decision"]
    Appeal = models["Appeal"]

    with db.begin():
        case = (
            db.query(Case)
            .filter(Case.case_id == case_id)
            .with_for_update()
            .first()
        )

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if case.case_status != "DECIDED":
            raise HTTPException(
                status_code=409,
                detail="An appeal can only be submitted for a decided case",
            )

        submission = db.query(Submission).filter(
            Submission.submission_id == case.submission_id
        ).first()

        if not submission or submission.learner_id != learner_id:
            raise HTTPException(
                status_code=403,
                detail="Only the learner who owns this case can appeal",
            )

        original = (
            db.query(Decision)
            .filter(
                Decision.case_id == case_id,
                Decision.decision_stage == "INITIAL",
            )
            .order_by(Decision.decided_at.desc())
            .first()
        )

        if not original:
            raise HTTPException(
                status_code=409,
                detail="No initial decision exists for this case",
            )

        if original.decision_type != "ACADEMIC_MISCONDUCT":
            raise HTTPException(
                status_code=409,
                detail="Only an academic misconduct decision can be appealed",
            )

        existing = db.query(Appeal).filter(
            Appeal.case_id == case_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="An appeal has already been submitted for this case",
            )

        now = datetime.utcnow()
        appeal_number = (
            db.query(func.count(Appeal.appeal_id))
            .filter(Appeal.case_id == case_id)
            .scalar()
            or 0
        ) + 1

        appeal_id = f"APL-{case_id}-{appeal_number:02d}"

        appeal = Appeal(
            appeal_id=appeal_id,
            case_id=case_id,
            original_decision_id=original.decision_id,
            submitted_by_learner_id=learner_id,
            appeal_reason=appeal_reason.strip(),
            appeal_status="SUBMITTED",
            submitted_at=now,
            due_at=now + timedelta(days=14),
            outcome=None,
            resolved_at=None,
        )

        db.add(appeal)
        case.case_status = "APPEALED"

        add_history(
            db, case_id,
            "LEARNER", learner_id,
            "APPEAL", appeal_id,
            "APPEAL_SUBMITTED",
            "Learner submitted an appeal against the initial decision",
            {
                "original_decision_id": original.decision_id,
                "appeal_status": "SUBMITTED",
            },
        )

        db.flush()

    return appeal


def resolve_appeal(db, appeal_id, reviewer_id, outcome, rationale):
    models = get_models()
    Appeal = models["Appeal"]
    Case = models["Case"]
    Submission = models["Submission"]
    Reviewer = models["Reviewer"]
    Conflict = models["Conflict"]
    Decision = models["Decision"]
    AppealReview = models["AppealReview"]

    with db.begin():
        appeal = (
            db.query(Appeal)
            .filter(Appeal.appeal_id == appeal_id)
            .with_for_update()
            .first()
        )

        if not appeal:
            raise HTTPException(status_code=404, detail="Appeal not found")

        if appeal.appeal_status not in ("SUBMITTED", "ASSIGNED", "UNDER_REVIEW"):
            raise HTTPException(
                status_code=409,
                detail="This appeal is not available for review",
            )

        case = (
            db.query(Case)
            .filter(Case.case_id == appeal.case_id)
            .with_for_update()
            .first()
        )

        submission = db.query(Submission).filter(
            Submission.submission_id == case.submission_id
        ).first()

        reviewer = (
            db.query(Reviewer)
            .filter(Reviewer.reviewer_id == reviewer_id)
            .with_for_update()
            .first()
        )

        if not reviewer or not reviewer.is_active:
            raise HTTPException(
                status_code=404,
                detail="Active reviewer not found",
            )

        original = db.query(Decision).filter(
            Decision.decision_id == appeal.original_decision_id
        ).first()

        if not original:
            raise HTTPException(
                status_code=409,
                detail="Original decision could not be found",
            )

        if original.reviewer_id == reviewer_id:
            raise HTTPException(
                status_code=409,
                detail="The original decision-maker cannot review the appeal",
            )

        conflict_query = db.query(Conflict).filter(
            Conflict.reviewer_id == reviewer_id,
            Conflict.is_active == True,
        )

        conflicts = conflict_query.all()

        for conflict in conflicts:
            learner_match = (
                conflict.learner_id is not None
                and conflict.learner_id == submission.learner_id
            )
            assessment_match = (
                conflict.assessment_id is not None
                and conflict.assessment_id == submission.assessment_id
            )

            if learner_match or assessment_match:
                raise HTTPException(
                    status_code=409,
                    detail="Reviewer has a conflict of interest for this appeal",
                )

        previous_review = db.query(AppealReview).filter(
            AppealReview.appeal_id == appeal_id
        ).first()

        if previous_review:
            raise HTTPException(
                status_code=409,
                detail="An independent appeal review already exists",
            )

        now = datetime.utcnow()

        review = AppealReview(
            appeal_id=appeal_id,
            reviewer_id=reviewer_id,
            outcome=outcome,
            rationale=rationale.strip(),
            reviewed_at=now,
        )
        db.add(review)

        reassessment = Decision(
            case_id=appeal.case_id,
            reviewer_id=reviewer_id,
            decision_type=outcome,
            decision_stage="REASSESSMENT",
            rationale=rationale.strip(),
            decided_at=now,
            supersedes_decision_id=original.decision_id,
        )
        db.add(reassessment)

        appeal.appeal_status = "RESOLVED"
        appeal.outcome = outcome
        appeal.resolved_at = now

        case.case_status = "CLOSED"
        case.closed_at = now
        case.closure_reason = f"Appeal resolved: {outcome}"

        add_history(
            db, appeal.case_id,
            "REVIEWER", reviewer_id,
            "APPEAL", appeal_id,
            "APPEAL_RESOLVED",
            "Independent reviewer resolved the learner appeal",
            {
                "outcome": outcome,
                "original_decision_id": original.decision_id,
                "reassessment_decision_type": outcome,
            },
        )

        db.flush()

    return {
        "appeal_id": appeal_id,
        "status": "RESOLVED",
        "outcome": outcome,
        "reassessment_decision_id": reassessment.decision_id,
        "reviewer_id": reviewer_id,
    }