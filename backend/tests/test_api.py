import os
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["ASTRA_DATABASE_URL"] = "sqlite://"

from app.database import Base, get_db
from app.main import app
from app.services.research_service import ResearchService


class FakeResearchService(ResearchService):
    def run(self, db: Session, user_id: int, query: str):
        from app.models import Citation, Memory, ResearchSession, Source, Summary

        research = ResearchSession(user_id=user_id, query=query, status="completed")
        db.add(research)
        db.flush()

        source = Source(
            research_id=research.id,
            title="Example Source",
            url="https://example.com",
            content="A" * 200,
        )
        db.add(source)
        db.flush()

        summary = Summary(research_id=research.id, content="Summary content")
        citation = Citation(
            research_id=research.id,
            source_id=source.id,
            marker="[1]",
            excerpt="A" * 120,
        )
        memory = Memory(research_id=research.id, chunk="A" * 200, source_url=source.url, score=1.0)
        db.add_all([summary, citation, memory])
        db.commit()
        db.refresh(research)
        db.refresh(summary)
        db.refresh(citation)
        return research, summary, [citation]


SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db] = override_get_db
app.state.research_service = FakeResearchService()

client = TestClient(app)


def login_headers() -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "strong-password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_research_endpoints() -> None:
    headers = login_headers()

    create_response = client.post(
        "/api/research",
        json={"query": "AI in healthcare"},
        headers=headers,
    )
    assert create_response.status_code == 200
    research_id = create_response.json()["research_id"]

    list_response = client.get("/api/research", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    detail_response = client.get(f"/api/research/{research_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["summary"]

    sources_response = client.get(f"/api/sources/{research_id}", headers=headers)
    assert sources_response.status_code == 200
    assert len(sources_response.json()) == 1

    memory_response = client.get(f"/api/memory/{research_id}", headers=headers)
    assert memory_response.status_code == 200
    assert len(memory_response.json()) == 1
