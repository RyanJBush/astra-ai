from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResearchCreate(BaseModel):
    query: str


class ResearchRead(BaseModel):
    id: int
    query: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceRead(BaseModel):
    id: int
    title: str
    url: str
    content: str

    model_config = {"from_attributes": True}


class CitationRead(BaseModel):
    marker: str
    excerpt: str
    source_id: int

    model_config = {"from_attributes": True}


class MemoryRead(BaseModel):
    id: int
    chunk: str
    source_url: str
    score: float

    model_config = {"from_attributes": True}


class ResearchDetail(BaseModel):
    research: ResearchRead
    summary: str
    citations: list[CitationRead]


class ResearchResult(BaseModel):
    research_id: int
    summary: str
    citations: list[CitationRead]
