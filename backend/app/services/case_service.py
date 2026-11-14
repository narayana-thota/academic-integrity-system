
from sqlalchemy import desc

from app.database import Base


def get_case_models():
    return {
        "Case": Base.classes.cases,
        "Submission": Base.classes.submissions,
        "Learner": Base.classes.learners,
        "Report": Base.classes.similarity_reports,
        "Event": Base.classes.case_events,
        "Evidence": Base.classes.evidence_items,
        "CaseEvidence": Base.classes.case_evidence,
        "Assignment": Base.classes.reviewer_assignments,
        "Reviewer": Base.classes.reviewers,
        "Decision": Base.classes.decisions,
        "Appeal": Base.classes.appeals,
    }


def list_cases(
    db,
    page=1,
    page_size=20,
    case_status=None,
    priority=None,
    learner_id=None,
):
    m = get_case_models()

    Case = m["Case"]
    Submission = m["Submission"]
    Learner = m["Learner"]
    Report = m["Report"]

    query = (
        db.query(Case, Learner, Report)
        .join(Submission, Case.submission_id == Submission.submission_id)
        .join(Learner, Submission.learner_id == Learner.learner_id)
        .join(Report, Case.report_id == Report.report_id)
    )

    if case_status:
        query = query.filter(Case.case_status == case_status)

    if priority:
        query = query.filter(Case.priority == priority)

    if learner_id is not None:
        query = query.filter(Submission.learner_id == learner_id)

    total = query.count()

    rows = (
        query.order_by(desc(Case.created_at), Case.case_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []

    for case, learner, report in rows:
        results.append({
            "case_id": case.case_id,
            "submission_id": case.submission_id,
            "report_id": case.report_id,
            "case_status": case.case_status,
            "priority": case.priority,
            "created_at": case.created_at,
            "due_at": case.due_at,
            "closed_at": case.closed_at,
            "learner_code": learner.learner_code,
            "learner_name": learner.full_name,
            "similarity_score": float(report.similarity_score),
            "review_action": report.review_action,
        })

    return total, results


def get_case_detail(db, case_id):
    m = get_case_models()

    Case = m["Case"]
    Submission = m["Submission"]
    Learner = m["Learner"]
    Report = m["Report"]
    Event = m["Event"]
    Evidence = m["Evidence"]
    CaseEvidence = m["CaseEvidence"]
    Assignment = m["Assignment"]
    Reviewer = m["Reviewer"]
    Decision = m["Decision"]
    Appeal = m["Appeal"]

    case = db.query(Case).filter(
        Case.case_id == case_id
    ).one_or_none()

    if case is None:
        return None

    submission = db.query(Submission).filter(
        Submission.submission_id == case.submission_id
    ).one()

    learner = db.query(Learner).filter(
        Learner.learner_id == submission.learner_id
    ).one()

    report = db.query(Report).filter(
        Report.report_id == case.report_id
    ).one()

    events = (
        db.query(Event)
        .filter(Event.case_id == case_id)
        .order_by(Event.occurred_at.asc(), Event.event_id.asc())
        .all()
    )

    evidence_rows = (
        db.query(Evidence)
        .join(
            CaseEvidence,
            Evidence.evidence_id == CaseEvidence.evidence_id
        )
        .filter(CaseEvidence.case_id == case_id)
        .order_by(CaseEvidence.linked_at.asc())
        .all()
    )

    assignment_rows = (
        db.query(Assignment, Reviewer)
        .join(Reviewer, Assignment.reviewer_id == Reviewer.reviewer_id)
        .filter(Assignment.case_id == case_id)
        .order_by(Assignment.assigned_at.asc())
        .all()
    )

    decisions = (
        db.query(Decision)
        .filter(Decision.case_id == case_id)
        .order_by(Decision.decided_at.asc(), Decision.decision_id.asc())
        .all()
    )

    appeals = (
        db.query(Appeal)
        .filter(Appeal.case_id == case_id)
        .order_by(Appeal.submitted_at.asc())
        .all()
    )

    return {
        "case_id": case.case_id,
        "submission_id": case.submission_id,
        "report_id": case.report_id,
        "case_status": case.case_status,
        "priority": case.priority,
        "created_at": case.created_at,
        "due_at": case.due_at,
        "closed_at": case.closed_at,
        "learner_code": learner.learner_code,
        "learner_name": learner.full_name,
        "similarity_score": float(report.similarity_score),
        "review_action": report.review_action,
        "rule_id": case.rule_id,
        "closure_reason": case.closure_reason,

        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "event_description": e.event_description,
                "actor_reference": e.actor_reference,
                "occurred_at": e.occurred_at,
            }
            for e in events
        ],

        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "evidence_type": e.evidence_type,
                "description": e.description,
                "version": e.version,
                "added_by": e.added_by,
                "created_at": e.created_at,
            }
            for e in evidence_rows
        ],

        "assignments": [
            {
                "assignment_id": a.assignment_id,
                "reviewer_id": a.reviewer_id,
                "reviewer_name": r.full_name,
                "assignment_status": a.assignment_status,
                "assigned_at": a.assigned_at,
                "ended_at": a.ended_at,
            }
            for a, r in assignment_rows
        ],

        "decisions": [
            {
                "decision_id": d.decision_id,
                "reviewer_id": d.reviewer_id,
                "decision_type": d.decision_type,
                "decision_stage": d.decision_stage,
                "rationale": d.rationale,
                "decided_at": d.decided_at,
            }
            for d in decisions
        ],

        "appeals": [
            {
                "appeal_id": a.appeal_id,
                "appeal_status": a.appeal_status,
                "appeal_reason": a.appeal_reason,
                "outcome": a.outcome,
                "submitted_at": a.submitted_at,
                "resolved_at": a.resolved_at,
            }
            for a in appeals
        ],
    }
