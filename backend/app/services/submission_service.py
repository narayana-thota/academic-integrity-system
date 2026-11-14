
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import Base


def get_submission_models():
    return (
        Base.classes.submissions,
        Base.classes.learners,
        Base.classes.assessments,
        Base.classes.similarity_reports,
    )


def list_submissions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    learner_id: int | None = None,
    assessment_id: int | None = None,
    status: str | None = None,
):
    Submission, Learner, Assessment, Report = get_submission_models()

    query = db.query(Submission)

    if learner_id is not None:
        query = query.filter(Submission.learner_id == learner_id)

    if assessment_id is not None:
        query = query.filter(Submission.assessment_id == assessment_id)

    if status is not None:
        query = query.filter(Submission.status == status)

    total = query.count()

    submissions = (
        query.order_by(Submission.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, submissions


def get_submission_by_id(db: Session, submission_id: str):
    Submission, Learner, Assessment, Report = get_submission_models()

    statement = (
        select(Submission)
        .where(Submission.submission_id == submission_id)
    )

    return db.execute(statement).scalar_one_or_none()
