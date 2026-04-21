from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    research_sessions: Mapped[list["ResearchSession"]] = relationship(back_populates="user")
    workspace: Mapped["Workspace"] = relationship(back_populates="users")


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="planning", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_sessions.id"),
        nullable=True,
    )
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped[User] = relationship(back_populates="research_sessions")
    sources: Mapped[list["Source"]] = relationship(back_populates="research_session")
    summary: Mapped["Summary"] = relationship(back_populates="research_session", uselist=False)
    citations: Mapped[list["Citation"]] = relationship(back_populates="research_session")
    memory_entries: Mapped[list["Memory"]] = relationship(back_populates="research_session")
    trace_events: Mapped[list["ResearchTraceEvent"]] = relationship(
        back_populates="research_session"
    )
    agent_metrics: Mapped[list["AgentRunMetric"]] = relationship(
        back_populates="research_session"
    )
    workspace: Mapped["Workspace"] = relationship(back_populates="research_sessions")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(2048))
    content: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(64), default="news")
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)

    research_session: Mapped[ResearchSession] = relationship(back_populates="sources")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), unique=True)
    content: Mapped[str] = mapped_column(Text)
    structured_report: Mapped[str] = mapped_column(Text, default="")
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    research_session: Mapped[ResearchSession] = relationship(back_populates="summary")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    marker: Mapped[str] = mapped_column(String(32))
    excerpt: Mapped[str] = mapped_column(Text)

    research_session: Mapped[ResearchSession] = relationship(back_populates="citations")


class Memory(Base):
    __tablename__ = "memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    chunk: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(2048))
    score: Mapped[float] = mapped_column(Float, default=0.0)

    research_session: Mapped[ResearchSession] = relationship(back_populates="memory_entries")


class ResearchTraceEvent(Base):
    __tablename__ = "research_trace_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    stage: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(32), default="completed")
    detail: Mapped[str] = mapped_column(Text, default="")
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    research_session: Mapped[ResearchSession] = relationship(back_populates="trace_events")


class AgentRunMetric(Base):
    __tablename__ = "agent_run_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    research_session: Mapped[ResearchSession] = relationship(back_populates="agent_metrics")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    users: Mapped[list[User]] = relationship(back_populates="workspace")
    research_sessions: Mapped[list[ResearchSession]] = relationship(back_populates="workspace")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="workspace")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="audit_logs")
