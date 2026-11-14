from sqlalchemy import func

from app.database import Base


def get_models():
    return {
        "Learner": Base.classes.learners,
        "Assessment": Base.classes.assessments,
        "Submission": Base.classes.submissions,
        "Report": Base.classes.similarity_reports,
        "Case": Base.classes.cases,
        "Evidence": Base.classes.evidence_items,
        "Reviewer": Base.classes.reviewers,
        "Assignment": Base.classes.reviewer_assignments,
        "Decision": Base.classes.decisions,
        "Appeal": Base.classes.appeals,
        "AppealReview": Base.classes.appeal_reviews,
    }


def count_rows(db, model):
    return db.query(func.count()).select_from(model).scalar() or 0


def grouped_counts(db, model, column):
    rows = (
        db.query(column, func.count())
        .group_by(column)
        .all()
    )
    return {
        str(key) if key is not None else "UNSPECIFIED": count
        for key, count in rows
    }


def get_dashboard_summary(db):
    m = get_models()

    active_assignment = m["Assignment"].assignment_status == "ACTIVE"

    reviewer_workload = (
        db.query(
            m["Reviewer"].reviewer_id,
            m["Reviewer"].reviewer_code,
            m["Reviewer"].full_name,
            m["Reviewer"].max_active_cases,
            func.count(m["Assignment"].assignment_id).label("active_cases"),
        )
        .outerjoin(
            m["Assignment"],
            (m["Reviewer"].reviewer_id == m["Assignment"].reviewer_id)
            & active_assignment,
        )
        .filter(m["Reviewer"].is_active == True)
        .group_by(
            m["Reviewer"].reviewer_id,
            m["Reviewer"].reviewer_code,
            m["Reviewer"].full_name,
            m["Reviewer"].max_active_cases,
        )
        .order_by(func.count(m["Assignment"].assignment_id).desc())
        .limit(10)
        .all()
    )

    total_cases = count_rows(db, m["Case"])
    closed_cases = (
        db.query(func.count())
        .select_from(m["Case"])
        .filter(m["Case"].case_status == "CLOSED")
        .scalar() or 0
    )

    return {
        "totals": {
            "learners": count_rows(db, m["Learner"]),
            "assessments": count_rows(db, m["Assessment"]),
            "submissions": count_rows(db, m["Submission"]),
            "similarity_reports": count_rows(db, m["Report"]),
            "cases": total_cases,
            "evidence_items": count_rows(db, m["Evidence"]),
            "reviewers": count_rows(db, m["Reviewer"]),
            "decisions": count_rows(db, m["Decision"]),
            "appeals": count_rows(db, m["Appeal"]),
            "appeal_reviews": count_rows(db, m["AppealReview"]),
        },
        "case_metrics": {
            "by_status": grouped_counts(
                db, m["Case"], m["Case"].case_status
            ),
            "by_priority": grouped_counts(
                db, m["Case"], m["Case"].priority
            ),
            "closed": closed_cases,
            "not_closed": total_cases - closed_cases,
        },
        "decision_metrics": {
            "by_type": grouped_counts(
                db, m["Decision"], m["Decision"].decision_type
            ),
            "by_stage": grouped_counts(
                db, m["Decision"], m["Decision"].decision_stage
            ),
        },
        "appeal_metrics": {
            "by_status": grouped_counts(
                db, m["Appeal"], m["Appeal"].appeal_status
            ),
            "by_outcome": grouped_counts(
                db, m["Appeal"], m["Appeal"].outcome
            ),
        },
        "reviewer_workload": [
            {
                "reviewer_id": row.reviewer_id,
                "reviewer_code": row.reviewer_code,
                "name": row.full_name,
                "active_cases": row.active_cases,
                "max_active_cases": row.max_active_cases,
                "capacity_remaining": max(
                    0, row.max_active_cases - row.active_cases
                ),
            }
            for row in reviewer_workload
        ],
    }
