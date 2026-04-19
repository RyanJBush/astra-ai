from sqlalchemy.orm import Session

from app.models.memory import MemoryEntry
from app.schemas.memory import MemoryCreate


class MemoryService:
    """Persistence adapter for long-term memory and FAISS indexing hooks."""

    async def create_memory(self, db: Session, payload: MemoryCreate) -> MemoryEntry:
        item = MemoryEntry(
            topic=payload.topic,
            content=payload.content,
            source_url=str(payload.source_url),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    async def list_memories(self, db: Session) -> list[MemoryEntry]:
        return db.query(MemoryEntry).order_by(MemoryEntry.created_at.desc()).all()
