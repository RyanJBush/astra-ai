import pytest
from app.config import settings
from app.models import Citation, Source, User
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from app.services.citations import CitationSystem
from app.services.memory_store import MemoryStore, SimpleEmbeddings
from app.services.reporting import ReportBuilder
from app.services.scraper import Scraper
from app.services.search import SearchTool
from app.services.summarizer import SummarizationAgent
from app.services.tool_registry import ToolRegistry
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt


class _FakeResponse:
    def __init__(self, payload: object, text: str = "") -> None:
        self._payload = payload
        self.text = text
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True

    def json(self) -> object:
        return self._payload


def test_citation_system_builds_markers_and_excerpts() -> None:
    citations = CitationSystem().build(
        [
            {"content": "A" * 300},
            {"content": "B" * 30},
        ]
    )
    assert citations[0]["marker"] == "[1]"
    assert citations[0]["source_index"] == 0
    assert citations[0]["excerpt"] == "A" * 220
    assert citations[1]["marker"] == "[2]"
    assert citations[1]["source_index"] == 1
    assert citations[1]["excerpt"] == "B" * 30


def test_summarizer_formats_numbered_output() -> None:
    summary = SummarizationAgent().summarize(
        "AI safety",
        [{"title": "Doc", "content": "C" * 250}],
    )
    assert summary.startswith("Research topic: AI safety")
    assert "- [1] Doc: " in summary
    assert ("C" * 180) in summary


def test_search_tool_returns_first_three_links(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _FakeResponse(
        ["query", [], [], ["https://a", "https://b", "https://c", "https://d"]]
    )

    def fake_get(url: str, timeout: int) -> _FakeResponse:
        assert "climate+change" in url
        assert timeout == 10
        return response

    monkeypatch.setattr("app.services.search.requests.get", fake_get)
    links = SearchTool().search("climate change")
    assert response.raise_for_status_called is True
    assert links == ["https://a", "https://b", "https://c"]


def test_search_tool_handles_unexpected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.search.requests.get",
        lambda *_args, **_kwargs: _FakeResponse({}),
    )
    links = SearchTool().search("query")
    assert links == []


def test_scraper_extracts_title_and_combines_paragraphs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = """
    <html>
      <head><title> Example Title </title></head>
      <body><p>First.</p><p>Second.</p><p></p></body>
    </html>
    """
    response = _FakeResponse([], text=html)
    monkeypatch.setattr("app.services.scraper.requests.get", lambda *_args, **_kwargs: response)
    title, content = Scraper().extract("https://example.com")
    assert response.raise_for_status_called is True
    assert title == "Example Title"
    assert content == "First. Second."


def test_scraper_falls_back_to_url_when_title_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _FakeResponse([], text="<html><body><p>Hello</p></body></html>")
    monkeypatch.setattr("app.services.scraper.requests.get", lambda *_args, **_kwargs: response)
    title, content = Scraper().extract("https://fallback.com")
    assert title == "https://fallback.com"
    assert content == "Hello"


def test_tool_registry_permissions_and_stage_enforcement() -> None:
    registry = ToolRegistry()
    assert registry.allowed_tools_for_role("ADMIN") == registry.ROLE_POLICIES["admin"]
    assert registry.allowed_tools_for_role("unknown") == set()
    registry.ensure_stage_allowed("user", "planning")
    with pytest.raises(PermissionError, match="Missing tools: planner"):
        registry.ensure_stage_allowed("viewer", "planning")


def test_password_hashing_and_verification() -> None:
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert verify_password("secret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_contains_subject_and_role() -> None:
    token = create_access_token("alice@example.com", "admin")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "alice@example.com"
    assert payload["role"] == "admin"


class _FakeQuery:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def filter(self, *_args, **_kwargs) -> "_FakeQuery":
        return self

    def first(self) -> User | None:
        return self._user


class _FakeDb:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def query(self, *_args, **_kwargs) -> _FakeQuery:
        return _FakeQuery(self._user)


def test_get_current_user_missing_credentials_raises_401() -> None:
    with pytest.raises(HTTPException, match="Missing token") as exc:
        get_current_user(None, _FakeDb(None))
    assert exc.value.status_code == 401


def test_get_current_user_invalid_token_raises_401() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-jwt")
    with pytest.raises(HTTPException, match="Invalid token") as exc:
        get_current_user(credentials, _FakeDb(None))
    assert exc.value.status_code == 401


def test_get_current_user_user_not_found_raises_401() -> None:
    token = create_access_token("missing@example.com", "user")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException, match="User not found") as exc:
        get_current_user(credentials, _FakeDb(None))
    assert exc.value.status_code == 401


def test_get_current_user_success() -> None:
    user = User(id=1, email="found@example.com", hashed_password="x", role="user")
    token = create_access_token(user.email, user.role)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current = get_current_user(credentials, _FakeDb(user))
    assert current.email == user.email


def test_require_role_blocks_unauthorized_user() -> None:
    dependency = require_role("admin")
    with pytest.raises(HTTPException, match="Insufficient role") as exc:
        dependency(User(id=1, email="u@example.com", hashed_password="x", role="user"))
    assert exc.value.status_code == 403


def test_report_builder_summary_and_metrics_branches() -> None:
    builder = ReportBuilder()
    source = Source(
        id=1,
        research_id=1,
        title="Claim",
        url="https://example.com",
        content="content",
        source_type="news",
        credibility_score=0.95,
    )
    citation = Citation(id=1, research_id=1, source_id=1, marker="[1]", excerpt="excerpt")
    report = builder.build("query", [source], [citation], [])
    summary_text = builder.to_summary_text(report)
    assert "Findings:" in summary_text
    assert "Conclusion:" in summary_text
    metrics = builder.metrics(report, [source], [citation])
    assert metrics["citation_coverage_score"] == 1.0
    assert metrics["contradiction_rate"] == 0.0


def test_report_builder_metrics_with_multiple_sources_and_contradictions() -> None:
    builder = ReportBuilder()
    sources = [
        Source(
            id=1,
            research_id=1,
            title="A",
            url="https://example.com/a",
            content="content a",
            source_type="news",
            credibility_score=0.9,
        ),
        Source(
            id=2,
            research_id=1,
            title="B",
            url="https://example.com/b",
            content="content b",
            source_type="official_docs",
            credibility_score=0.6,
        ),
    ]
    report = {
        "contradictions": [{"reason": "inconsistent outcomes"}],
        "evidence_coverage": {"score": 0.5},
    }
    metrics = builder.metrics(report, sources, [])
    assert metrics["source_count"] == 2
    assert metrics["citation_coverage_score"] == 0.0
    assert metrics["contradiction_rate"] == 1.0


def test_report_builder_open_question_fallback_and_review_flag() -> None:
    builder = ReportBuilder()
    source = Source(
        id=1,
        research_id=1,
        title="Low confidence claim",
        url="https://example.com",
        content="x",
        source_type="news",
        credibility_score=0.5,
    )
    report = builder.build("q", [source], [], [])
    assert report["open_questions"]
    assert report["review_required"] is True


def test_report_builder_disclaimer_for_low_coverage_and_summary_disclaimer() -> None:
    builder = ReportBuilder()
    report = {
        "executive_summary": "Summary",
        "findings": [],
        "open_questions": [],
        "disclaimer": (
            "Limited evidence coverage; more sources are required before relying on findings."
        ),
        "conclusion": "Tentative",
    }
    text = builder.to_summary_text(report)
    assert "Disclaimer:" in text


def test_require_role_allows_authorized_user() -> None:
    dependency = require_role("admin", "user")
    user = User(id=1, email="u@example.com", hashed_password="x", role="admin")
    assert dependency(user) is user


def test_get_current_user_missing_subject_claim_raises_401() -> None:
    token = jwt.encode({"role": "user"}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException, match="Invalid token") as exc:
        get_current_user(credentials, _FakeDb(None))
    assert exc.value.status_code == 401


def test_search_tool_uses_raise_for_status(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _FakeResponse(["q", [], [], []])
    monkeypatch.setattr("app.services.search.requests.get", lambda *_args, **_kwargs: response)
    SearchTool().search("any")
    assert response.raise_for_status_called is True


def test_scraper_limits_content_and_title_length(monkeypatch: pytest.MonkeyPatch) -> None:
    oversized_title = "T" * 800
    oversized_paragraph = "P" * 7000
    response = _FakeResponse(
        [],
        text=(
            f"<html><head><title>{oversized_title}</title></head>"
            f"<body><p>{oversized_paragraph}</p></body></html>"
        ),
    )
    monkeypatch.setattr("app.services.scraper.requests.get", lambda *_args, **_kwargs: response)
    title, content = Scraper().extract("https://example.com")
    assert len(title) == 500
    assert len(content) == 5000


def test_simple_embeddings_are_stable_and_fixed_width() -> None:
    embeddings = SimpleEmbeddings()
    vector = embeddings.embed_query("abc")
    assert len(vector) == 8
    assert vector == embeddings.embed_documents(["abc"])[0]


def test_memory_store_add_chunks_updates_vector_count() -> None:
    store = MemoryStore()
    initial_total = store._store.index.ntotal
    store.add_chunks(["chunk one", "chunk two"], research_id=7, source_url="https://example.com")
    assert store._store.index.ntotal == initial_total + 2
