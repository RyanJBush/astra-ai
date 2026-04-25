import json
from time import perf_counter

from sqlalchemy.orm import Session

from app.models import (
    AgentRunMetric,
    Citation,
    Memory,
    ResearchSession,
    ResearchTraceEvent,
    Source,
    Summary,
)
from app.services.citations import CitationSystem
from app.services.memory_store import MemoryStore
from app.services.pii_redactor import PIIRedactor
from app.services.planner import PlannerAgent
from app.services.reporting import ReportBuilder
from app.services.scraper import Scraper
from app.services.search import SearchTool
from app.services.summarizer import SummarizationAgent
from app.services.tool_registry import ToolRegistry
from app.services.validator import ValidationLayer


class ResearchService:
    STAGES = ("planning", "searching", "extracting", "validating", "synthesizing")

    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.search_tool = SearchTool()
        self.scraper = Scraper()
        self.validator = ValidationLayer()
        self.summarizer = SummarizationAgent()
        self.citation_system = CitationSystem()
        self.memory = MemoryStore()
        self.report_builder = ReportBuilder()
        self.tool_registry = ToolRegistry()
        self.pii_redactor = PIIRedactor()

    def run(
        self,
        db: Session,
        user_id: int,
        query: str,
        role: str = "researcher",
        workspace_id: int | None = None,
        *,
        depth: int = 2,
        breadth: int = 3,
        recency_days: int | None = None,
        max_sources: int = 5,
        allow_domains: list[str] | None = None,
        deny_domains: list[str] | None = None,
        parent_session_id: int | None = None,
        version: int = 1,
    ) -> tuple[ResearchSession, Summary, list[Citation]]:
        research = ResearchSession(
            user_id=user_id,
            query=query,
            status="planning",
            parent_session_id=parent_session_id,
            version=version,
            workspace_id=workspace_id,
        )
        db.add(research)
        db.flush()

        try:
            planning_started = perf_counter()
            self.tool_registry.ensure_stage_allowed(role, "planning")
            self._start_stage(db, research, "planning", "Building research plan")
            plan_steps = self._run_agent(
                db,
                research.id,
                "planner",
                lambda: self.planner.plan(query, breadth=breadth),
            )
            self._record_stage(db, research, "planning", planning_started, "Plan generated")

            searching_started = perf_counter()
            self.tool_registry.ensure_stage_allowed(role, "searching")
            self._start_stage(db, research, "searching", "Running web discovery")
            discovered_urls: list[str] = []
            active_queries = list(plan_steps)
            for iteration in range(max(1, depth)):
                iteration_queries = active_queries if iteration == 0 else active_queries[:breadth]
                discovered_urls_iteration: list[str] = []
                for step in iteration_queries:
                    search_queries = self.planner.generate_search_queries(
                        step,
                        recency_days=recency_days,
                    )
                    for search_query in search_queries:
                        try:
                            discovered_urls_iteration.extend(
                                self._run_agent(
                                    db,
                                    research.id,
                                    "search",
                                    lambda q=search_query: self.search_tool.search(q),
                                )
                            )
                        except Exception:
                            continue
                discovered_urls.extend(discovered_urls_iteration)
                if iteration == max(1, depth) - 1:
                    break
                deduped_preview = list(dict.fromkeys(discovered_urls_iteration))
                source_payloads_preview: list[dict[str, str]] = []
                for url in deduped_preview[:max_sources]:
                    try:
                        title, content = self._run_agent(
                            db,
                            research.id,
                            "extractor",
                            lambda source_url=url: self.scraper.extract(source_url),
                        )
                    except Exception:
                        continue
                    source_payloads_preview.append({"title": title, "url": url, "content": content})
                validated_preview = self._run_agent(
                    db,
                    research.id,
                    "validator",
                    lambda preview=source_payloads_preview: self.validator.filter_sources(
                        preview,
                        allow_domains=allow_domains,
                        deny_domains=deny_domains,
                    ),
                )
                preview_report = self.report_builder.build(query, [], [], [])
                if validated_preview:
                    preview_report = self.report_builder.build(
                        query,
                        [
                            Source(
                                id=index + 1,
                                research_id=research.id,
                                title=str(source["title"]),
                                url=str(source["url"]),
                                content=str(source["content"]),
                                source_type=str(source["source_type"]),
                                credibility_score=float(source["credibility_score"]),
                            )
                            for index, source in enumerate(validated_preview)
                        ],
                        [],
                        [],
                    )
                evidence_score = float(preview_report["evidence_coverage"]["score"])
                if evidence_score >= 0.6:
                    break
                active_queries = self.planner.generate_follow_up_queries(
                    query,
                    list(preview_report["evidence_coverage"]["unsupported_claims"]),
                )
            deduped_urls = list(dict.fromkeys(discovered_urls))
            self._record_stage(
                db,
                research,
                "searching",
                searching_started,
                f"Collected {len(deduped_urls)} candidate sources",
            )

            extracting_started = perf_counter()
            self.tool_registry.ensure_stage_allowed(role, "extracting")
            self._start_stage(db, research, "extracting", "Extracting source content")
            source_payloads: list[dict[str, str]] = []
            for url in deduped_urls:
                try:
                    title, content = self._run_agent(
                        db,
                        research.id,
                        "extractor",
                        lambda source_url=url: self.scraper.extract(source_url),
                    )
                except Exception:
                    continue
                source_payloads.append({"title": title, "url": url, "content": content})
            self._record_stage(
                db,
                research,
                "extracting",
                extracting_started,
                f"Extracted {len(source_payloads)} source payloads",
            )

            validating_started = perf_counter()
            self.tool_registry.ensure_stage_allowed(role, "validating")
            self._start_stage(
                db,
                research,
                "validating",
                "Scoring sources and checking consistency",
            )
            validated_sources = self._run_agent(
                db,
                research.id,
                "validator",
                lambda: self.validator.filter_sources(
                    source_payloads,
                    allow_domains=allow_domains,
                    deny_domains=deny_domains,
                ),
            )[:max_sources]
            contradictions = self._run_agent(
                db,
                research.id,
                "validator",
                lambda: self.validator.detect_contradictions(validated_sources),
            )
            self._record_stage(
                db,
                research,
                "validating",
                validating_started,
                (
                    f"Validated {len(validated_sources)} sources with "
                    f"{len(contradictions)} contradictions"
                ),
            )

            source_rows: list[Source] = []
            pii_redactions_total = 0
            for source_payload in validated_sources:
                redacted_content, redaction_stats = self.pii_redactor.redact(
                    str(source_payload["content"])
                )
                pii_redactions_total += redaction_stats["total"]
                content_chunk = redacted_content[:500]
                row = Source(
                    research_id=research.id,
                    title=str(source_payload["title"]),
                    url=str(source_payload["url"]),
                    content=redacted_content,
                    source_type=str(source_payload["source_type"]),
                    credibility_score=float(source_payload["credibility_score"]),
                )
                db.add(row)
                source_rows.append(row)
                self.memory.add_chunks(
                    [content_chunk],
                    research.id,
                    str(source_payload["url"]),
                )
                db.add(
                    Memory(
                        research_id=research.id,
                        chunk=content_chunk,
                        source_url=str(source_payload["url"]),
                        score=1.0,
                    )
                )
            db.flush()

            citation_rows: list[Citation] = []
            citation_payloads = self._run_agent(
                db,
                research.id,
                "citation",
                lambda: self.citation_system.build(
                    [
                        {
                            "title": source.title,
                            "url": source.url,
                            "content": source.content,
                        }
                        for source in source_rows
                    ]
                ),
            )
            for citation_payload in citation_payloads:
                source_index = int(citation_payload["source_index"])
                if source_index >= len(source_rows):
                    continue
                citation = Citation(
                    research_id=research.id,
                    source_id=source_rows[source_index].id,
                    marker=str(citation_payload["marker"]),
                    excerpt=str(citation_payload["excerpt"]),
                )
                db.add(citation)
                citation_rows.append(citation)
            db.flush()

            synthesizing_started = perf_counter()
            self.tool_registry.ensure_stage_allowed(role, "synthesizing")
            self._start_stage(db, research, "synthesizing", "Drafting structured report")
            report = self._run_agent(
                db,
                research.id,
                "synthesis",
                lambda: self.report_builder.build(
                    query,
                    source_rows,
                    citation_rows,
                    contradictions,
                    compliance={"pii_redactions": pii_redactions_total},
                ),
            )
            summary_text = self.report_builder.to_summary_text(report)
            summary = Summary(
                research_id=research.id,
                content=summary_text,
                structured_report=json.dumps(report),
                requires_review=bool(report.get("review_required", False)),
                review_reason=report.get("disclaimer"),
            )
            db.add(summary)
            self._record_stage(
                db,
                research,
                "synthesizing",
                synthesizing_started,
                f"Synthesized report with {len(report['findings'])} findings",
            )

            research.status = "complete"
            self._record_stage(db, research, "complete", perf_counter(), "Research complete")
            db.commit()
            db.refresh(research)
            db.refresh(summary)
            for citation in citation_rows:
                db.refresh(citation)
            return research, summary, citation_rows
        except Exception as exc:
            research.status = "failed"
            error_category = self._error_category(exc)
            db.add(
                ResearchTraceEvent(
                    research_id=research.id,
                    stage="failed",
                    state="failed",
                    detail=str(exc),
                    error_category=error_category,
                    latency_ms=0.0,
                )
            )
            db.commit()
            raise

    def metrics(
        self,
        summary: Summary,
        sources: list[Source],
        citations: list[Citation],
        trace_events: list[ResearchTraceEvent] | None = None,
    ) -> dict[str, float | int]:
        report = json.loads(summary.structured_report) if summary.structured_report else {}
        if not report:
            stage_latency_ms = self._stage_latency(trace_events or [])
            return {
                "source_count": len(sources),
                "average_credibility_score": 0.0,
                "citation_coverage_score": 0.0,
                "evidence_coverage_score": 0.0,
                "fact_support_ratio": 0.0,
                "contradiction_rate": 0.0,
                "total_latency_ms": round(sum(stage_latency_ms.values()), 3),
                "stage_latency_ms": stage_latency_ms,
            }
        base_metrics = self.report_builder.metrics(report, sources, citations)
        stage_latency_ms = self._stage_latency(trace_events or [])
        base_metrics["stage_latency_ms"] = stage_latency_ms
        base_metrics["total_latency_ms"] = round(sum(stage_latency_ms.values()), 3)
        return base_metrics

    def pause(self, db: Session, research: ResearchSession) -> ResearchSession:
        research.status = "paused"
        research.is_paused = True
        db.add(
            ResearchTraceEvent(
                research_id=research.id,
                stage="paused",
                state="completed",
                detail="Research paused by user",
                latency_ms=0.0,
            )
        )
        db.commit()
        db.refresh(research)
        return research

    def resume(self, db: Session, research: ResearchSession) -> ResearchSession:
        research.status = "planning"
        research.is_paused = False
        db.add(
            ResearchTraceEvent(
                research_id=research.id,
                stage="planning",
                state="in_progress",
                detail="Research resumed by user",
                latency_ms=0.0,
            )
        )
        db.commit()
        db.refresh(research)
        return research

    def _start_stage(
        self,
        db: Session,
        research: ResearchSession,
        stage: str,
        detail: str,
    ) -> None:
        research.status = stage
        db.add(
            ResearchTraceEvent(
                research_id=research.id,
                stage=stage,
                state="in_progress",
                detail=detail,
                error_category=None,
                latency_ms=0.0,
            )
        )

    def _record_stage(
        self,
        db: Session,
        research: ResearchSession,
        stage: str,
        started_at: float,
        detail: str,
    ) -> None:
        research.status = stage
        db.add(
            ResearchTraceEvent(
                research_id=research.id,
                stage=stage,
                state="completed",
                detail=detail,
                error_category=None,
                latency_ms=round((perf_counter() - started_at) * 1000, 3),
            )
        )

    def _stage_latency(self, trace_events: list[ResearchTraceEvent]) -> dict[str, float]:
        latency_by_stage = {stage: 0.0 for stage in self.STAGES}
        for event in trace_events:
            if event.stage in latency_by_stage and event.state == "completed":
                latency_by_stage[event.stage] = max(latency_by_stage[event.stage], event.latency_ms)
        return latency_by_stage

    def replay(self, research: ResearchSession, trace_events: list[ResearchTraceEvent]) -> dict:
        timeline = [
            {
                "stage": event.stage,
                "state": event.state,
                "detail": event.detail,
                "error_category": event.error_category,
                "latency_ms": event.latency_ms,
                "created_at": event.created_at,
            }
            for event in sorted(trace_events, key=lambda row: row.created_at)
        ]
        stage_counts: dict[str, int] = {}
        error_categories: list[str] = []
        for event in trace_events:
            stage_counts[event.stage] = stage_counts.get(event.stage, 0) + 1
            if event.error_category and event.error_category not in error_categories:
                error_categories.append(event.error_category)
        return {
            "research_id": research.id,
            "status": research.status,
            "timeline": timeline,
            "stage_counts": stage_counts,
            "error_categories": sorted(error_categories),
        }

    def _error_category(self, exc: Exception) -> str:
        if isinstance(exc, PermissionError):
            return "permission"
        if isinstance(exc, TimeoutError):
            return "timeout"
        return "pipeline"

    def _run_agent(
        self,
        db: Session,
        research_id: int,
        agent_name: str,
        fn,
        retries: int = 1,
    ):
        attempts = 0
        started = perf_counter()
        last_exc: Exception | None = None
        for _ in range(retries + 1):
            attempts += 1
            try:
                result = fn()
                self._record_agent_metric(
                    db,
                    research_id,
                    agent_name,
                    "completed",
                    attempts,
                    perf_counter() - started,
                    None,
                )
                return result
            except Exception as exc:  # noqa: PERF203
                last_exc = exc
        self._record_agent_metric(
            db,
            research_id,
            agent_name,
            "failed",
            attempts,
            perf_counter() - started,
            str(last_exc) if last_exc else "unknown",
        )
        raise last_exc if last_exc else RuntimeError("Agent execution failed")

    def _record_agent_metric(
        self,
        db: Session,
        research_id: int,
        agent_name: str,
        status: str,
        attempts: int,
        latency_s: float,
        error: str | None,
    ) -> None:
        db.add(
            AgentRunMetric(
                research_id=research_id,
                agent_name=agent_name,
                status=status,
                attempts=attempts,
                latency_ms=round(latency_s * 1000, 3),
                error=error,
            )
        )
