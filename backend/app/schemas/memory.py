from datetime import datetime

from pydantic import BaseModel, HttpUrl


class MemoryCreate(BaseModel):
    topic: str
    content: str
    source_url: HttpUrl


class MemoryRead(MemoryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
