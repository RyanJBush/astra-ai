from datetime import UTC, datetime, timedelta

import pytest
from app.models import AgentRunMetric, ResearchSession, ResearchTraceEvent
from app.services.research_service import ResearchService


class _FakeDb:
    def __init__(self) -> None:
        self.rows: list[object] = []

    def add(self, row: object) -> None:
        self.rows.append(row)


def test_error_category_classifies_known_error_types() -> None:
    service = ResearchService()
    assert service._error_category(PermissionError("nope")) == "permission"
    assert service._error_category(TimeoutError("slow")) == "timeout"
    assert service._error_category(RuntimeError("boom")) == "pipeline"


def test_stage_latency_uses_completed_events_only_and_keeps_max_per_stage() -> None:
    service = ResearchService()
    events = [
        ResearchTraceEvent(stage="planning", state="completed", latency_ms=8.0),
        ResearchTraceEvent(stage="planning", state="completed", latency_ms=12.0),
        ResearchTraceEvent(stage="planning", state="in_progress", latency_ms=99.0),
        ResearchTraceEvent(stage="searching", state="completed", latency_ms=4.5),
        ResearchTraceEvent(stage="unknown", state="completed", latency_ms=100.0),
    ]

    latency = service._stage_latency(events)

    assert latency["planning"] == 12.0
    assert latency["searching"] == 4.5
    assert latency["extracting"] == 0.0
    assert "unknown" not in latency


def test_replay_sorts_timeline_and_deduplicates_error_categories() -> None:
    service = ResearchService()
    now = datetime.now(UTC)
    research = ResearchSession(id=42, user_id=1, query="q", status="failed")
    events = [
        ResearchTraceEvent(
            stage="validating",
            state="failed",
            detail="bad data",
            error_category="pipeline",
            latency_ms=1.0,
            created_at=now + timedelta(seconds=5),
        ),
        ResearchTraceEvent(
            stage="planning",
            state="completed",
            detail="done",
            error_category=None,
            latency_ms=2.0,
            created_at=now,
        ),
        ResearchTraceEvent(
            stage="searching",
            state="failed",
            detail="timeout",
            error_category="timeout",
            latency_ms=3.0,
            created_at=now + timedelta(seconds=2),
        ),
        ResearchTraceEvent(
            stage="extracting",
            state="failed",
            detail="again",
            error_category="pipeline",
            latency_ms=3.0,
            created_at=now + timedelta(seconds=3),
        ),
    ]

    replay = service.replay(research, events)

    assert [item["stage"] for item in replay["timeline"]] == [
        "planning",
        "searching",
        "extracting",
        "validating",
    ]
    assert replay["stage_counts"]["planning"] == 1
    assert replay["stage_counts"]["validating"] == 1
    assert replay["error_categories"] == ["pipeline", "timeout"]


def test_run_agent_records_completed_metric_after_retries() -> None:
    service = ResearchService()
    db = _FakeDb()
    attempts = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = service._run_agent(db, research_id=1, agent_name="search", fn=flaky, retries=2)

    assert result == "ok"
    assert attempts["count"] == 3
    metric = db.rows[-1]
    assert isinstance(metric, AgentRunMetric)
    assert metric.status == "completed"
    assert metric.attempts == 3
    assert metric.error is None


def test_run_agent_records_failed_metric_when_retries_exhausted() -> None:
    service = ResearchService()
    db = _FakeDb()

    def always_fail() -> str:
        raise RuntimeError("hard failure")

    with pytest.raises(RuntimeError, match="hard failure"):
        service._run_agent(
            db,
            research_id=1,
            agent_name="validator",
            fn=always_fail,
            retries=1,
        )

    metric = db.rows[-1]
    assert isinstance(metric, AgentRunMetric)
    assert metric.status == "failed"
    assert metric.attempts == 2
    assert metric.error == "hard failure"
