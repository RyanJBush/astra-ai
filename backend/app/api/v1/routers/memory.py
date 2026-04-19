from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.memory import MemoryCreate, MemoryRead
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])
service = MemoryService()


@router.post("", response_model=MemoryRead)
async def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)) -> MemoryRead:
    return await service.create_memory(db, payload)


@router.get("", response_model=list[MemoryRead])
async def list_memory(db: Session = Depends(get_db)) -> list[MemoryRead]:
    return await service.list_memories(db)
