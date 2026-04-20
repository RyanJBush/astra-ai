from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    research_sessions: Mapped[list["ResearchSession"]] = relationship(back_populates="user")


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="planning")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    user: Mapped[User] = relationship(back_populates="research_sessions")
    sources: Mapped[list["Source"]] = relationship(back_populates="research_session")
    summary: Mapped["Summary"] = relationship(back_populates="research_session", uselist=False)
    citations: Mapped[list["Citation"]] = relationship(back_populates="research_session")
    memory_entries: Mapped[list["Memory"]] = relationship(back_populates="research_session")
    trace_events: Mapped[list["ResearchTraceEvent"]] = relationship(
        back_populates="research_session"
    )


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
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    research_session: Mapped[ResearchSession] = relationship(back_populates="trace_events")
