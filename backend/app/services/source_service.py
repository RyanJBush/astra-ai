from sqlalchemy.orm import Session

from app.models.research import ResearchSource
from app.schemas.source import SourceItem


class SourceService:
    """Returns latest validated sources captured from research runs."""

    async def list_sources(self, db: Session, limit: int = 25) -> list[SourceItem]:
        rows = (
            db.query(ResearchSource)
            .order_by(ResearchSource.credibility_score.desc())
            .limit(limit)
            .all()
        )
        return [
            SourceItem(
                title=row.title,
                url=row.url,
                snippet=row.snippet,
                relevance_score=row.relevance_score,
                credibility_score=row.credibility_score,
            )
            for row in rows
        ]
