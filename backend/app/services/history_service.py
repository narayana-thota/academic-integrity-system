from fastapi import HTTPException

from app.database import Base


def get_models():
    return {
        "Case": Base.classes.cases,
        "Event": Base.classes.case_events,
        "Audit": Base.classes.audit_logs,
    }


def get_case_timeline(db, case_id, page=1, page_size=100):
    models = get_models()
    Case = models["Case"]
    Event = models["Event"]

    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    query = db.query(Event).filter(Event.case_id == case_id)
    total = query.count()

    events = (
        query.order_by(Event.occurred_at.asc(), Event.event_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "case_id": case_id,
        "items": events,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def list_audit_logs(
    db,
    page=1,
    page_size=50,
    case_id=None,
    entity_type=None,
    entity_reference=None,
    actor_reference=None,
    action=None,
):
    Audit = get_models()["Audit"]
    query = db.query(Audit)

    if case_id:
        query = query.filter(Audit.case_id == case_id)
    if entity_type:
        query = query.filter(Audit.entity_type == entity_type)
    if entity_reference:
        query = query.filter(Audit.entity_reference == entity_reference)
    if actor_reference:
        query = query.filter(Audit.actor_reference == actor_reference)
    if action:
        query = query.filter(Audit.action == action)

    total = query.count()
    rows = (
        query.order_by(Audit.created_at.desc(), Audit.audit_id.desc())
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


def get_audit_log(db, audit_id):
    Audit = get_models()["Audit"]
    row = db.query(Audit).filter(Audit.audit_id == audit_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return row
