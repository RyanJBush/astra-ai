from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 5


class CitationItem(BaseModel):
    index: int
    title: str
    url: HttpUrl
    credibility_score: float


class ResearchSourceRead(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    relevance_score: float
    credibility_score: float


class ResearchResponse(BaseModel):
    id: int
    query: str
    summary: str
    citations: list[CitationItem]
    sources: list[ResearchSourceRead]
    created_at: datetime


class ResearchListResponse(BaseModel):
    id: int
    query: str
    status: str
    created_at: datetime
