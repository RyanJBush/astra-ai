import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import (
    AgentRunMetric,
    AuditLog,
    Citation,
    Memory,
    ResearchSession,
    ResearchTraceEvent,
    Source,
    Summary,
    User,
    Workspace,
)
from app.schemas import (
    AgentMetricRead,
    AuditLogRead,
    LoginRequest,
    MemoryRead,
    ResearchComplianceRead,
    ResearchCreate,
    ResearchDetail,
    ResearchMetricsRead,
    ResearchRead,
    ResearchReplayRead,
    ResearchResult,
    ResearchTraceRead,
    SourceRead,
    TokenResponse,
    WorkspaceRead,
)
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from app.services.research_service import ResearchService

app = FastAPI(title="Astra AI Backend")
app.state.research_service = ResearchService()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.jwt_secret == "change-me":
        print("WARNING: ASTRA_JWT_SECRET is using the default insecure value.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        workspace = _get_or_create_workspace(db, payload.email)
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role="researcher",
            workspace_id=workspace.id,
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
    user: User = Depends(require_role("admin", "researcher")),
) -> ResearchResult:
    _enforce_daily_quota(db, user.id)
    research, summary, citations = app.state.research_service.run(
        db,
        user.id,
        payload.query,
        role=user.role,
        workspace_id=user.workspace_id,
        depth=payload.depth,
        breadth=payload.breadth,
        recency_days=payload.recency_days,
        max_sources=payload.max_sources,
        allow_domains=payload.allow_domains,
        deny_domains=payload.deny_domains,
    )
    _log_audit(db, user, "research.create", "research_session", research.id, payload.query)
    report = json.loads(summary.structured_report) if summary.structured_report else {}
    return ResearchResult(
        research_id=research.id,
        summary=summary.content,
        citations=citations,
        report=report,
    )


@app.post("/api/research/{research_id}/pause", response_model=ResearchRead)
def pause_research(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> ResearchRead:
    research = _get_research_or_404(db, research_id, user.id)
    updated = app.state.research_service.pause(db, research)
    _log_audit(db, user, "research.pause", "research_session", research_id, "Paused by user")
    return updated


@app.post("/api/research/{research_id}/resume", response_model=ResearchRead)
def resume_research(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> ResearchRead:
    research = _get_research_or_404(db, research_id, user.id)
    updated = app.state.research_service.resume(db, research)
    _log_audit(db, user, "research.resume", "research_session", research_id, "Resumed by user")
    return updated


@app.post("/api/research/{research_id}/retry", response_model=ResearchResult)
def retry_research(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> ResearchResult:
    previous = _get_research_or_404(db, research_id, user.id)
    _enforce_daily_quota(db, user.id)
    research, summary, citations = app.state.research_service.run(
        db,
        user.id,
        previous.query,
        role=user.role,
        workspace_id=user.workspace_id,
        parent_session_id=previous.id,
        version=previous.version + 1,
    )
    _log_audit(
        db,
        user,
        "research.retry",
        "research_session",
        research.id,
        f"Retry from {research_id}",
    )
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
        requires_review=bool(summary.requires_review) if summary else False,
        review_reason=summary.review_reason if summary else None,
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
    trace_events = db.query(ResearchTraceEvent).filter(
        ResearchTraceEvent.research_id == research_id
    ).all()
    if summary is None:
        return ResearchMetricsRead(
            source_count=len(sources),
            average_credibility_score=0.0,
            citation_coverage_score=0.0,
            evidence_coverage_score=0.0,
            fact_support_ratio=0.0,
            contradiction_rate=0.0,
            total_latency_ms=0.0,
            stage_latency_ms={},
        )
    return ResearchMetricsRead.model_validate(
        app.state.research_service.metrics(summary, sources, citations, trace_events)
    )


@app.get("/api/research/{research_id}/agent-metrics", response_model=list[AgentMetricRead])
def get_research_agent_metrics(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AgentRunMetric]:
    _validate_research_owner(db, research_id, user.id)
    return (
        db.query(AgentRunMetric)
        .filter(AgentRunMetric.research_id == research_id)
        .order_by(AgentRunMetric.created_at.asc())
        .all()
    )


@app.get("/api/research/{research_id}/compliance", response_model=ResearchComplianceRead)
def get_research_compliance(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResearchComplianceRead:
    _validate_research_owner(db, research_id, user.id)
    summary = db.query(Summary).filter(Summary.research_id == research_id).first()
    report = json.loads(summary.structured_report) if summary and summary.structured_report else {}
    compliance = report.get("compliance", {})
    return ResearchComplianceRead(
        research_id=research_id,
        pii_redactions=int(compliance.get("pii_redactions", 0)),
        review_required=bool(summary.requires_review) if summary else False,
    )


@app.get("/api/research/{research_id}/replay", response_model=ResearchReplayRead)
def replay_research_run(
    research_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResearchReplayRead:
    research = _get_research_or_404(db, research_id, user.id)
    trace_events = (
        db.query(ResearchTraceEvent)
        .filter(ResearchTraceEvent.research_id == research_id)
        .order_by(ResearchTraceEvent.created_at.asc())
        .all()
    )
    return ResearchReplayRead.model_validate(
        app.state.research_service.replay(research, trace_events)
    )


@app.get("/api/workspaces/current", response_model=WorkspaceRead)
def get_current_workspace(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkspaceRead:
    workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@app.get("/api/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == user.workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )


@app.get("/api/research/{research_id}/export")
def export_research_report(
    research_id: int,
    format: str = "markdown",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _validate_research_owner(db, research_id, user.id)
    summary = db.query(Summary).filter(Summary.research_id == research_id).first()
    if summary is None or not summary.structured_report:
        raise HTTPException(status_code=404, detail="Report not found")
    report = json.loads(summary.structured_report)
    if format == "markdown":
        markdown = app.state.research_service.report_builder.to_markdown(report)
        return PlainTextResponse(markdown, media_type="text/markdown")
    if format == "json":
        return JSONResponse(report)
    raise HTTPException(status_code=400, detail="Unsupported export format")


def _validate_research_owner(db: Session, research_id: int, user_id: int) -> None:
    _get_research_or_404(db, research_id, user_id)


def _get_research_or_404(db: Session, research_id: int, user_id: int) -> ResearchSession:
    research = (
        db.query(ResearchSession)
        .filter(ResearchSession.id == research_id, ResearchSession.user_id == user_id)
        .first()
    )
    if research is None:
        raise HTTPException(status_code=404, detail="Research not found")
    return research


def _get_or_create_workspace(db: Session, email: str) -> Workspace:
    workspace_name = f"{email.split('@')[0]}-workspace"
    workspace = db.query(Workspace).filter(Workspace.name == workspace_name).first()
    if workspace is None:
        workspace = Workspace(name=workspace_name)
        db.add(workspace)
        db.flush()
    return workspace


def _log_audit(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: int | None,
    detail: str,
) -> None:
    if user.workspace_id is None:
        return
    db.add(
        AuditLog(
            workspace_id=user.workspace_id,
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
        )
    )
    db.commit()


def _enforce_daily_quota(db: Session, user_id: int) -> None:
    window_start = datetime.now(timezone.utc) - timedelta(days=1)
    submissions_last_day = (
        db.query(ResearchSession)
        .filter(ResearchSession.user_id == user_id, ResearchSession.created_at >= window_start)
        .count()
    )
    if submissions_last_day >= settings.daily_research_quota:
        raise HTTPException(status_code=429, detail="Daily research quota exceeded")
