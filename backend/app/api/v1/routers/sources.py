from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.source import SourceItem
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])
service = SourceService()


@router.get("", response_model=list[SourceItem])
async def list_sources(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[SourceItem]:
    return await service.list_sources(db, limit=limit)
