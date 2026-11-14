
from sqlalchemy import select

from app.database import Base


def get_report_models():
    return (
        Base.classes.similarity_reports,
        Base.classes.report_matches,
        Base.classes.cases,
    )


def list_reports(
    db,
    page=1,
    page_size=20,
    review_action=None,
    report_category=None,
):
    Report, Match, Case = get_report_models()

    query = db.query(Report)

    if review_action:
        query = query.filter(Report.review_action == review_action)

    if report_category:
        query = query.filter(Report.report_category == report_category)

    total = query.count()

    reports = (
        query.order_by(Report.generated_at.desc(), Report.report_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, reports


def get_report_by_id(db, report_id):
    Report, Match, Case = get_report_models()

    statement = select(Report).where(
        Report.report_id == report_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_report_matches(db, report_id):
    Report, Match, Case = get_report_models()

    return (
        db.query(Match)
        .filter(Match.report_id == report_id)
        .order_by(Match.match_sequence.asc())
        .all()
    )


def get_case_for_report(db, report_id):
    Report, Match, Case = get_report_models()

    return (
        db.query(Case)
        .filter(Case.report_id == report_id)
        .one_or_none()
    )
