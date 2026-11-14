
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import reflect_database, get_db
from app.api.v1.system import router as system_router
from app.api.v1.submissions import router as submissions_router
from app.api.v1.similarity_reports import router as similarity_reports_router
from app.api.v1.cases import router as cases_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.reviewers import router as reviewers_router
from app.api.v1.decisions import router as decisions_router
from app.api.v1 import appeals
from app.api.v1 import case_evidence
from app.api.v1 import history
from app.api.v1 import dashboard
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reflect existing MySQL schema during application startup.
    reflect_database()
    yield


app = FastAPI(
    title="Academic Integrity Case Management API",
    description=(
        "API for academic integrity similarity cases, "
        "evidence, reviewer assignments, decisions and appeals."
    ),
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API v1 routers.
app.include_router(
    system_router,
    prefix="/api/v1"
)

app.include_router(
    submissions_router,
    prefix="/api/v1"
)

app.include_router(
    similarity_reports_router,
    prefix="/api/v1"
)

app.include_router(
    cases_router,
    prefix="/api/v1"
)

app.include_router(
    evidence_router,
    prefix="/api/v1"
)

app.include_router(
    reviewers_router,
    prefix="/api/v1"
)

app.include_router(
    decisions_router,
    prefix="/api/v1",
)

app.include_router(appeals.router, prefix="/api/v1")

app.include_router(case_evidence.router, prefix="/api/v1")

app.include_router(history.router, prefix="/api/v1")

app.include_router(dashboard.router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Academic Integrity API is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.get("/health/db", tags=["Health"])
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "academic_integrity"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )
