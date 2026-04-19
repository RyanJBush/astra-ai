from sqlalchemy.orm import Session

from app.models.research import ResearchRun, ResearchSource


class ResearchRepository:
    def create_run(self, db: Session, query: str, summary: str, status: str = "completed") -> ResearchRun:
        run = ResearchRun(query=query, summary=summary, status=status)
        db.add(run)
        db.flush()
        return run

    def add_sources(self, db: Session, run: ResearchRun, sources: list[dict]) -> None:
        for src in sources:
            db.add(
                ResearchSource(
                    research_run_id=run.id,
                    title=src["title"],
                    url=src["url"],
                    snippet=src["snippet"],
                    extracted_content=src["content"],
                    relevance_score=src["relevance_score"],
                    credibility_score=src["credibility_score"],
                )
            )

    def list_runs(self, db: Session) -> list[ResearchRun]:
        return db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).all()

    def get_run(self, db: Session, run_id: int) -> ResearchRun | None:
        return db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
