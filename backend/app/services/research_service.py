import logging

from sqlalchemy.orm import Session

from app.agents.planner_agent import PlannerAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.repositories.research_repository import ResearchRepository
from app.schemas.research import CitationItem, ResearchListResponse, ResearchRequest, ResearchResponse, ResearchSourceRead
from app.tools.scraper_tool import ScraperTool
from app.tools.web_search_tool import WebSearchTool
from app.utils.citations import build_citations
from app.validators.source_validator import SourceValidator

logger = logging.getLogger(__name__)


class ResearchService:
    """Coordinates planner, search, scraping, validation, and summarization."""

    def __init__(
        self,
        planner: PlannerAgent | None = None,
        search_tool: WebSearchTool | None = None,
        scraper: ScraperTool | None = None,
        validator: SourceValidator | None = None,
        summarizer: SummarizerAgent | None = None,
        repository: ResearchRepository | None = None,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.search_tool = search_tool or WebSearchTool()
        self.scraper = scraper or ScraperTool()
        self.validator = validator or SourceValidator()
        self.summarizer = summarizer or SummarizerAgent()
        self.repository = repository or ResearchRepository()

    async def run_research(self, db: Session, payload: ResearchRequest) -> ResearchResponse:
        logger.info("research.start", extra={"query": payload.query})
        planned_queries = self.planner.plan_queries(payload.query)

        collected: list[dict] = []
        for planned in planned_queries:
            search_results = await self.search_tool.search(planned, max_results=payload.max_sources)
            for result in search_results:
                if any(existing["url"] == result["url"] for existing in collected):
                    continue
                content = await self.scraper.extract(result["url"])
                result["content"] = content
                result["relevance_score"] = min(len(result["snippet"]) / 240, 1.0)
                result["credibility_score"] = self.validator.score(result["url"], content)
                collected.append(result)
                if len(collected) >= payload.max_sources:
                    break
            if len(collected) >= payload.max_sources:
                break

        ranked = sorted(
            collected,
            key=lambda item: (item["credibility_score"] + item["relevance_score"]),
            reverse=True,
        )

        summary = self.summarizer.summarize(payload.query, ranked)

        run = self.repository.create_run(db, query=payload.query, summary=summary)
        self.repository.add_sources(db, run, ranked)
        db.commit()
        db.refresh(run)

        citations = [CitationItem(**item) for item in build_citations(ranked)]
        response_sources = [
            ResearchSourceRead(
                title=src["title"],
                url=src["url"],
                snippet=src["snippet"],
                relevance_score=src["relevance_score"],
                credibility_score=src["credibility_score"],
            )
            for src in ranked
        ]

        return ResearchResponse(
            id=run.id,
            query=run.query,
            summary=run.summary,
            citations=citations,
            sources=response_sources,
            created_at=run.created_at,
        )

    def list_research_runs(self, db: Session) -> list[ResearchListResponse]:
        runs = self.repository.list_runs(db)
        return [
            ResearchListResponse(
                id=run.id,
                query=run.query,
                status=run.status,
                created_at=run.created_at,
            )
            for run in runs
        ]

    def get_research_run(self, db: Session, run_id: int) -> ResearchResponse | None:
        run = self.repository.get_run(db, run_id)
        if not run:
            return None

        sorted_sources = sorted(
            run.sources,
            key=lambda src: (src.credibility_score + src.relevance_score),
            reverse=True,
        )
        source_dicts = [
            {
                "title": src.title,
                "url": src.url,
                "snippet": src.snippet,
                "credibility_score": src.credibility_score,
                "relevance_score": src.relevance_score,
            }
            for src in sorted_sources
        ]

        return ResearchResponse(
            id=run.id,
            query=run.query,
            summary=run.summary,
            citations=[CitationItem(**item) for item in build_citations(source_dicts)],
            sources=[ResearchSourceRead(**item) for item in source_dicts],
            created_at=run.created_at,
        )
