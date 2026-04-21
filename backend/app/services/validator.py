from urllib.parse import urlparse


class ValidationLayer:
    OFFICIAL_DOMAINS = ("gov", "edu")
    ACADEMIC_HINTS = ("arxiv.org", "acm.org", "ieee.org", "springer.com", "nature.com")
    FORUM_HINTS = ("reddit.com", "stackexchange.com", "quora.com")
    BLOG_HINTS = ("medium.com", "substack.com", "blog")
    NEWS_HINTS = ("reuters.com", "bbc.com", "nytimes.com", "apnews.com")

    POSITIVE_CLAIM_HINTS = (
        "is effective",
        "effective",
        "increases",
        "improves",
        "beneficial",
        "outperforms",
    )
    NEGATIVE_CLAIM_HINTS = (
        "is not effective",
        "ineffective",
        "does not increase",
        "doesn't increase",
        "does not improve",
        "doesn't improve",
        "worsens",
        "decreases",
        "harmful",
    )
    UNSAFE_CONTENT_HINTS = (
        "ignore previous instructions",
        "disregard instructions",
        "system prompt",
        "developer message",
    )

    def filter_sources(
        self,
        sources: list[dict[str, str]],
        allow_domains: list[str] | None = None,
        deny_domains: list[str] | None = None,
    ) -> list[dict[str, str | float]]:
        validated: list[dict[str, str | float]] = []
        normalized_allow = {domain.lower() for domain in (allow_domains or [])}
        normalized_deny = {domain.lower() for domain in (deny_domains or [])}
        seen_fingerprints: set[str] = set()
        for source in sources:
            content = source.get("content", "")
            url = source.get("url", "")
            if len(content) < 100 or not url.startswith("http"):
                continue
            if self.has_prompt_injection_signal(content):
                continue
            host = self._host(url)
            if normalized_deny and any(host.endswith(domain) for domain in normalized_deny):
                continue
            if normalized_allow and not any(host.endswith(domain) for domain in normalized_allow):
                continue
            fingerprint = self._dedupe_fingerprint(source.get("title", ""), url, content)
            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)
            source_type = self.classify_source_type(url)
            credibility_score = self.score_source_credibility(url, content, source_type)
            validated.append(
                {
                    "title": source.get("title", ""),
                    "url": url,
                    "content": content,
                    "source_type": source_type,
                    "credibility_score": credibility_score,
                }
            )
        return validated

    def classify_source_type(self, url: str) -> str:
        host = self._host(url)
        if any(host.endswith(f".{suffix}") for suffix in self.OFFICIAL_DOMAINS):
            return "official_docs"
        if any(hint in host for hint in self.ACADEMIC_HINTS):
            return "academic"
        if any(hint in host for hint in self.NEWS_HINTS):
            return "news"
        if any(hint in host for hint in self.FORUM_HINTS):
            return "forum"
        if any(hint in host for hint in self.BLOG_HINTS):
            return "blog"
        return "news"

    def score_source_credibility(self, url: str, content: str, source_type: str) -> float:
        base = {
            "official_docs": 0.95,
            "academic": 0.9,
            "news": 0.75,
            "blog": 0.55,
            "forum": 0.4,
        }.get(source_type, 0.5)
        https_bonus = 0.03 if url.startswith("https://") else 0.0
        length_bonus = 0.02 if len(content) > 1000 else 0.0
        score = min(1.0, base + https_bonus + length_bonus)
        return round(score, 3)

    def score_evidence_coverage(
        self,
        findings: list[dict[str, object]],
    ) -> dict[str, object]:
        if not findings:
            return {"supported_claims": 0, "total_claims": 0, "score": 0.0, "unsupported_claims": []}
        unsupported_claims = [
            str(finding.get("claim", ""))
            for finding in findings
            if not finding.get("support")
        ]
        supported = len(findings) - len(unsupported_claims)
        return {
            "supported_claims": supported,
            "total_claims": len(findings),
            "score": round(supported / len(findings), 3),
            "unsupported_claims": unsupported_claims,
        }

    def detect_contradictions(
        self,
        sources: list[dict[str, str | float]],
    ) -> list[dict[str, str | int]]:
        analyzed_sources = [
            {
                "content": str(source.get("content", "")).lower(),
                "title": str(source.get("title", "")),
            }
            for source in sources
        ]
        polarity_by_index: dict[int, tuple[bool, bool]] = {}
        for index, source in enumerate(analyzed_sources):
            content = source["content"]
            polarity_by_index[index] = (
                any(term in content for term in self.POSITIVE_CLAIM_HINTS),
                any(term in content for term in self.NEGATIVE_CLAIM_HINTS),
            )

        contradictions: list[dict[str, str | int]] = []
        for left_idx, left_source in enumerate(analyzed_sources):
            for right_idx in range(left_idx + 1, len(analyzed_sources)):
                right_source = analyzed_sources[right_idx]
                has_positive_left, has_negative_left = polarity_by_index[left_idx]
                has_positive_right, has_negative_right = polarity_by_index[right_idx]
                if (has_positive_left and has_negative_right) or (
                    has_negative_left and has_positive_right
                ):
                    contradictions.append(
                        {
                            "left_index": left_idx,
                            "right_index": right_idx,
                            "reason": "Opposing outcome language found across sources",
                            "left_claim": str(left_source.get("title", "")),
                            "right_claim": str(right_source.get("title", "")),
                        }
                    )
        return contradictions

    def evidence_coverage_score(self, findings: list[dict[str, object]]) -> float:
        coverage = self.score_evidence_coverage(findings)
        return float(coverage["score"])

    def _host(self, url: str) -> str:
        return (urlparse(url).hostname or "").lower()

    def _dedupe_fingerprint(self, title: str, url: str, content: str) -> str:
        normalized_title = str(title).strip().lower()
        normalized_url = str(url).strip().lower().split("#", maxsplit=1)[0]
        content_head = str(content).strip().lower()[:250]
        return f"{normalized_title}|{normalized_url}|{content_head}"

    def has_prompt_injection_signal(self, content: str) -> bool:
        lowered = str(content).lower()
        return any(hint in lowered for hint in self.UNSAFE_CONTENT_HINTS)
