from app.models import Citation, Source
from app.services.reporting import ReportBuilder
from app.services.validator import ValidationLayer


def test_source_classification_and_credibility() -> None:
    validator = ValidationLayer()
    source_type = validator.classify_source_type("https://www.nasa.gov/mission")
    score = validator.score_source_credibility(
        "https://www.nasa.gov/mission",
        "NASA released mission documentation with detailed methodology and findings. " * 25,
        source_type,
    )
    assert source_type == "official_docs"
    assert score >= 0.95


def test_detect_contradictions() -> None:
    validator = ValidationLayer()
    contradictions = validator.detect_contradictions(
        [
            {
                "title": "Study A",
                "url": "https://example.com/a",
                "content": "The treatment is effective and improves outcomes.",
                "source_type": "news",
                "credibility_score": 0.7,
            },
            {
                "title": "Study B",
                "url": "https://example.com/b",
                "content": "The treatment is not effective and worsens outcomes.",
                "source_type": "news",
                "credibility_score": 0.7,
            },
        ]
    )
    assert len(contradictions) == 1
    assert contradictions[0]["left_index"] == 0
    assert contradictions[0]["right_index"] == 1


def test_report_includes_claim_to_source_links_and_coverage() -> None:
    report_builder = ReportBuilder()
    sources = [
        Source(
            id=1,
            research_id=1,
            title="Claim One",
            url="https://example.com/1",
            content="Supporting content",
            source_type="news",
            credibility_score=0.8,
        )
    ]
    citations = [
        Citation(
            id=1,
            research_id=1,
            source_id=1,
            marker="[1]",
            excerpt="Supporting excerpt",
        )
    ]
    report = report_builder.build("demo query", sources, citations, [])
    assert report["findings"][0]["claim"] == "Claim One"
    assert report["findings"][0]["support"][0]["source_id"] == 1
    assert report["evidence_coverage"]["score"] == 1.0
