from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.research import ResearchListResponse, ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])
service = ResearchService()


@router.post("", response_model=ResearchResponse)
async def run_research(payload: ResearchRequest, db: Session = Depends(get_db)) -> ResearchResponse:
    return await service.run_research(db, payload)


@router.get("", response_model=list[ResearchListResponse])
def list_runs(db: Session = Depends(get_db)) -> list[ResearchListResponse]:
    return service.list_research_runs(db)


@router.get("/{run_id}", response_model=ResearchResponse)
def get_run(run_id: int, db: Session = Depends(get_db)) -> ResearchResponse:
    run = service.get_research_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run
