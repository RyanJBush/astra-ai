from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

RESEARCH_STATES = (
    "planning",
    "searching",
    "extracting",
    "validating",
    "synthesizing",
    "paused",
    "complete",
    "failed",
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResearchCreate(BaseModel):
    query: str
    depth: int = 2
    breadth: int = 3
    recency_days: int | None = 30
    max_sources: int = 5
    allow_domains: list[str] = Field(default_factory=list)
    deny_domains: list[str] = Field(default_factory=list)


class ResearchRead(BaseModel):
    id: int
    query: str
    status: str
    version: int
    is_paused: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceRead(BaseModel):
    id: int
    title: str
    url: str
    content: str
    source_type: str
    credibility_score: float

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
    report: dict
    requires_review: bool = False
    review_reason: str | None = None


class ResearchResult(BaseModel):
    research_id: int
    summary: str
    citations: list[CitationRead]
    report: dict


class ResearchTraceRead(BaseModel):
    stage: str
    state: str
    detail: str
    error_category: str | None = None
    latency_ms: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchMetricsRead(BaseModel):
    source_count: int
    average_credibility_score: float
    citation_coverage_score: float
    evidence_coverage_score: float
    fact_support_ratio: float
    contradiction_rate: float
    total_latency_ms: float
    stage_latency_ms: dict[str, float]


class ResearchReplayRead(BaseModel):
    research_id: int
    status: str
    timeline: list[ResearchTraceRead]
    stage_counts: dict[str, int]
    error_categories: list[str]


class WorkspaceRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    action: str
    resource_type: str
    resource_id: int | None
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentMetricRead(BaseModel):
    agent_name: str
    status: str
    attempts: int
    latency_ms: float
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchComplianceRead(BaseModel):
    research_id: int
    pii_redactions: int
    review_required: bool
