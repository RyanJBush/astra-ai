import json
from time import perf_counter

from sqlalchemy.orm import Session

from app.models import Citation, Memory, ResearchSession, ResearchTraceEvent, Source, Summary
from app.services.citations import CitationSystem
from app.services.memory_store import MemoryStore
from app.services.planner import PlannerAgent
from app.services.reporting import ReportBuilder
from app.services.scraper import Scraper
from app.services.search import SearchTool
from app.services.summarizer import SummarizationAgent
from app.services.validator import ValidationLayer


class ResearchService:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.search_tool = SearchTool()
        self.scraper = Scraper()
        self.validator = ValidationLayer()
        self.summarizer = SummarizationAgent()
        self.citation_system = CitationSystem()
        self.memory = MemoryStore()
        self.report_builder = ReportBuilder()

    def run(
        self,
        db: Session,
        user_id: int,
        query: str,
    ) -> tuple[ResearchSession, Summary, list[Citation]]:
        research = ResearchSession(user_id=user_id, query=query, status="planning")
        db.add(research)
        db.flush()

        try:
            planning_started = perf_counter()
            plan_steps = self.planner.plan(query)
            self._record_stage(db, research, "planning", planning_started, "Plan generated")

            searching_started = perf_counter()
            discovered_urls: list[str] = []
            for step in plan_steps:
                try:
                    discovered_urls.extend(self.search_tool.search(step))
                except Exception:
                    continue
            deduped_urls = list(dict.fromkeys(discovered_urls))
            self._record_stage(
                db,
                research,
                "searching",
                searching_started,
                f"Collected {len(deduped_urls)} candidate sources",
            )

            extracting_started = perf_counter()
            source_payloads: list[dict[str, str]] = []
            for url in deduped_urls:
                try:
                    title, content = self.scraper.extract(url)
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
            validated_sources = self.validator.filter_sources(source_payloads)[:5]
            contradictions = self.validator.detect_contradictions(validated_sources)
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
            for source_payload in validated_sources:
                content_chunk = str(source_payload["content"])[:500]
                row = Source(
                    research_id=research.id,
                    title=str(source_payload["title"]),
                    url=str(source_payload["url"]),
                    content=str(source_payload["content"]),
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
            citation_payloads = self.citation_system.build(
                [
                    {
                        "title": source.title,
                        "url": source.url,
                        "content": source.content,
                    }
                    for source in source_rows
                ]
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
            report = self.report_builder.build(query, source_rows, citation_rows, contradictions)
            summary_text = self.report_builder.to_summary_text(report)
            summary = Summary(
                research_id=research.id,
                content=summary_text,
                structured_report=json.dumps(report),
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
            db.add(
                ResearchTraceEvent(
                    research_id=research.id,
                    stage="failed",
                    state="failed",
                    detail=str(exc),
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
    ) -> dict[str, float | int]:
        report = json.loads(summary.structured_report) if summary.structured_report else {}
        if not report:
            return {
                "source_count": len(sources),
                "average_credibility_score": 0.0,
                "citation_coverage_score": 0.0,
                "evidence_coverage_score": 0.0,
                "contradiction_rate": 0.0,
            }
        return self.report_builder.metrics(report, sources, citations)

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
                latency_ms=round((perf_counter() - started_at) * 1000, 3),
            )
        )
