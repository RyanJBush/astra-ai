import json

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Citation, Memory, ResearchSession, ResearchTraceEvent, Source, Summary, User
from app.schemas import (
    LoginRequest,
    MemoryRead,
    ResearchCreate,
    ResearchDetail,
    ResearchMetricsRead,
    ResearchRead,
    ResearchResult,
    ResearchTraceRead,
    SourceRead,
    TokenResponse,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password
from app.services.research_service import ResearchService

app = FastAPI(title="Astra AI Backend")
app.state.research_service = ResearchService()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token)


@app.post("/api/research", response_model=ResearchResult)
def create_research(
    payload: ResearchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResearchResult:
    research, summary, citations = app.state.research_service.run(db, user.id, payload.query)
    report = json.loads(summary.structured_report) if summary.structured_report else {}
    return ResearchResult(
        research_id=research.id,
        summary=summary.content,
        citations=citations,
        report=report,
    )


@app.get("/api/research", response_model=list[ResearchRead])
def list_research(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ResearchSession]:
    return (
        db.query(ResearchSession)
        .filter(ResearchSession.user_id == user.id)
        .order_by(ResearchSession.created_at.desc())
        .all()
    )


@app.get("/api/research/{research_id}", response_model=ResearchDetail)
def get_research(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResearchDetail:
    research = (
        db.query(ResearchSession)
        .filter(ResearchSession.id == research_id, ResearchSession.user_id == user.id)
        .first()
    )
    if research is None:
        raise HTTPException(status_code=404, detail="Research not found")

    summary = db.query(Summary).filter(Summary.research_id == research_id).first()
    citations = db.query(Citation).filter(Citation.research_id == research_id).all()
    return ResearchDetail(
        research=research,
        summary=summary.content if summary else "",
        citations=citations,
        report=(
            json.loads(summary.structured_report)
            if summary and summary.structured_report
            else {}
        ),
    )


@app.get("/api/sources/{research_id}", response_model=list[SourceRead])
def get_sources(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Source]:
    _validate_research_owner(db, research_id, user.id)
    return db.query(Source).filter(Source.research_id == research_id).all()


@app.get("/api/memory/{research_id}", response_model=list[MemoryRead])
def get_memory(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Memory]:
    _validate_research_owner(db, research_id, user.id)
    return db.query(Memory).filter(Memory.research_id == research_id).all()


@app.get("/api/research/{research_id}/trace", response_model=list[ResearchTraceRead])
def get_research_trace(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ResearchTraceEvent]:
    _validate_research_owner(db, research_id, user.id)
    return (
        db.query(ResearchTraceEvent)
        .filter(ResearchTraceEvent.research_id == research_id)
        .order_by(ResearchTraceEvent.created_at.asc())
        .all()
    )


@app.get("/api/research/{research_id}/metrics", response_model=ResearchMetricsRead)
def get_research_metrics(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResearchMetricsRead:
    _validate_research_owner(db, research_id, user.id)
    summary = db.query(Summary).filter(Summary.research_id == research_id).first()
    sources = db.query(Source).filter(Source.research_id == research_id).all()
    citations = db.query(Citation).filter(Citation.research_id == research_id).all()
    if summary is None:
        return ResearchMetricsRead(
            source_count=len(sources),
            average_credibility_score=0.0,
            citation_coverage_score=0.0,
            evidence_coverage_score=0.0,
            contradiction_rate=0.0,
        )
    return ResearchMetricsRead.model_validate(
        app.state.research_service.metrics(summary, sources, citations)
    )


def _validate_research_owner(db: Session, research_id: int, user_id: int) -> None:
    research = (
        db.query(ResearchSession)
        .filter(ResearchSession.id == research_id, ResearchSession.user_id == user_id)
        .first()
    )
    if research is None:
        raise HTTPException(status_code=404, detail="Research not found")
