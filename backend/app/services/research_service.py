from sqlalchemy.orm import Session

from app.models import Citation, Memory, ResearchSession, Source, Summary
from app.services.citations import CitationSystem
from app.services.memory_store import MemoryStore
from app.services.planner import PlannerAgent
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

    def run(
        self,
        db: Session,
        user_id: int,
        query: str,
    ) -> tuple[ResearchSession, Summary, list[Citation]]:
        research = ResearchSession(user_id=user_id, query=query, status="processing")
        db.add(research)
        db.flush()

        source_payloads: list[dict[str, str]] = []
        for step in self.planner.plan(query):
            try:
                urls = self.search_tool.search(step)
            except Exception:
                continue
            for url in urls:
                try:
                    title, content = self.scraper.extract(url)
                except Exception:
                    continue
                source_payloads.append({"title": title, "url": url, "content": content})

        validated_sources = self.validator.filter_sources(source_payloads)[:5]
        source_rows: list[Source] = []
        for source_payload in validated_sources:
            row = Source(research_id=research.id, **source_payload)
            db.add(row)
            source_rows.append(row)
            self.memory.add_chunks(
                [source_payload["content"][:500]],
                research.id,
                source_payload["url"],
            )
            db.add(
                Memory(
                    research_id=research.id,
                    chunk=source_payload["content"][:500],
                    source_url=source_payload["url"],
                    score=1.0,
                )
            )

        summary_text = self.summarizer.summarize(query, validated_sources)
        summary = Summary(research_id=research.id, content=summary_text)
        db.add(summary)

        citation_rows: list[Citation] = []
        citation_payloads = self.citation_system.build(validated_sources)
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

        research.status = "completed"
        db.commit()
        db.refresh(research)
        db.refresh(summary)
        for citation in citation_rows:
            db.refresh(citation)
        return research, summary, citation_rows
