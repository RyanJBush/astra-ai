from app.models import Citation, Source
from app.services.reporting import ReportBuilder


def test_structured_report_contract_includes_core_fields() -> None:
    builder = ReportBuilder()
    source = Source(
        id=1,
        research_id=1,
        title="Policy memo claims governance benefits",
        url="https://example.com/policy",
        content="Detailed analysis of governance controls and outcomes.",
        source_type="news",
        credibility_score=0.82,
    )
    citation = Citation(
        id=1,
        research_id=1,
        source_id=1,
        marker="[1]",
        excerpt="governance controls and outcomes",
    )
    report = builder.build(
        query="Assess governance controls",
        sources=[source],
        citations=[citation],
        contradictions=[],
    )

    assert (
        report["executive_summary"]
        == "Automated research summary for: Assess governance controls"
    )
    assert "findings" in report
    assert "evidence_table" in report
    assert "source_comparison" in report
    assert "contradictions" in report
    assert "evidence_coverage" in report
    assert "open_questions" in report
    assert "conclusion" in report

    finding = report["findings"][0]
    assert finding["claim_id"] == "F-1"
    assert finding["support"][0]["marker"] == "[1]"
    assert finding["source_links"] == ["https://example.com/policy"]
    assert report["evidence_coverage"]["score"] == 1.0
