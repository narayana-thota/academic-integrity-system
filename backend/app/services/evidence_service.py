
from app.database import Base


def get_evidence_models():
    return (
        Base.classes.evidence_items,
        Base.classes.case_evidence,
    )


def list_evidence(
    db,
    page=1,
    page_size=20,
    case_id=None,
    evidence_type=None,
):
    Evidence, CaseEvidence = get_evidence_models()

    query = db.query(Evidence)

    if case_id:
        query = (
            query.join(
                CaseEvidence,
                Evidence.evidence_id == CaseEvidence.evidence_id
            )
            .filter(CaseEvidence.case_id == case_id)
        )

    if evidence_type:
        query = query.filter(
            Evidence.evidence_type == evidence_type
        )

    total = query.count()

    records = (
        query.order_by(
            Evidence.created_at.desc(),
            Evidence.evidence_id.asc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, records


def get_evidence_by_id(db, evidence_id):
    Evidence, CaseEvidence = get_evidence_models()

    return (
        db.query(Evidence)
        .filter(Evidence.evidence_id == evidence_id)
        .one_or_none()
    )


def get_evidence_cases(db, evidence_id):
    Evidence, CaseEvidence = get_evidence_models()

    return (
        db.query(CaseEvidence)
        .filter(CaseEvidence.evidence_id == evidence_id)
        .order_by(CaseEvidence.linked_at.asc())
        .all()
    )
