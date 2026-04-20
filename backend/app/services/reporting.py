from app.models import Citation, Source
from app.services.validator import ValidationLayer


class ReportBuilder:
    def __init__(self) -> None:
        self.validator = ValidationLayer()

    def build(
        self,
        query: str,
        sources: list[Source],
        citations: list[Citation],
        contradictions: list[dict[str, str | int]],
    ) -> dict:
        citation_by_source: dict[int, list[Citation]] = {}
        for citation in citations:
            citation_by_source.setdefault(citation.source_id, []).append(citation)

        findings: list[dict] = []
        for source in sources:
            support = [
                {
                    "source_id": source.id,
                    "marker": citation.marker,
                    "excerpt": citation.excerpt,
                    "url": source.url,
                }
                for citation in citation_by_source.get(source.id, [])
            ]
            findings.append(
                {
                    "claim": source.title,
                    "confidence": round(float(source.credibility_score), 3),
                    "support": support,
                }
            )

        evidence_score = self.validator.evidence_coverage_score(findings)
        contradiction_items = [
            {
                "claim_a": item["left_claim"],
                "claim_b": item["right_claim"],
                "reason": item["reason"],
                "source_indices": [item["left_index"], item["right_index"]],
            }
            for item in contradictions
        ]
        conclusion = (
            "Evidence is mixed; contradictory claims require additional validation."
            if contradiction_items
            else "Evidence is directionally consistent across current sources."
        )
        return {
            "executive_summary": f"Automated research summary for: {query}",
            "findings": findings,
            "evidence_table": [
                {
                    "source_id": source.id,
                    "title": source.title,
                    "source_type": source.source_type,
                    "credibility_score": source.credibility_score,
                    "url": source.url,
                }
                for source in sources
            ],
            "contradictions": contradiction_items,
            "evidence_coverage": {
                "supported_claims": sum(1 for finding in findings if finding["support"]),
                "total_claims": len(findings),
                "score": evidence_score,
            },
            "conclusion": conclusion,
        }

    def to_summary_text(self, report: dict) -> str:
        lines = [report["executive_summary"], ""]
        lines.append("Findings:")
        for finding in report["findings"]:
            claim = finding["claim"]
            confidence = finding["confidence"]
            markers = ", ".join(item["marker"] for item in finding["support"]) or "none"
            lines.append(f"- {claim} (confidence={confidence}, support={markers})")
        lines.append("")
        lines.append(f"Conclusion: {report['conclusion']}")
        return "\n".join(lines)

    def metrics(
        self,
        report: dict,
        sources: list[Source],
        citations: list[Citation],
    ) -> dict[str, float | int]:
        source_count = len(sources)
        citation_coverage = 0.0
        if source_count:
            covered_source_ids = {citation.source_id for citation in citations}
            citation_coverage = round(len(covered_source_ids) / source_count, 3)
        avg_credibility = (
            round(sum(source.credibility_score for source in sources) / source_count, 3)
            if source_count
            else 0.0
        )
        contradiction_rate = 0.0
        source_pair_count = source_count * (source_count - 1) / 2
        if source_pair_count > 0:
            contradiction_rate = round(
                min(1.0, len(report["contradictions"]) / source_pair_count),
                3,
            )
        return {
            "source_count": source_count,
            "average_credibility_score": avg_credibility,
            "citation_coverage_score": citation_coverage,
            "evidence_coverage_score": float(report["evidence_coverage"]["score"]),
            "contradiction_rate": contradiction_rate,
        }
