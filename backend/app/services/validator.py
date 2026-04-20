from urllib.parse import urlparse


class ValidationLayer:
    OFFICIAL_DOMAINS = ("gov", "edu")
    ACADEMIC_HINTS = ("arxiv.org", "acm.org", "ieee.org", "springer.com", "nature.com")
    FORUM_HINTS = ("reddit.com", "stackexchange.com", "quora.com")
    BLOG_HINTS = ("medium.com", "substack.com", "blog")
    NEWS_HINTS = ("reuters.com", "bbc.com", "nytimes.com", "apnews.com")

    POSITIVE_CLAIM_HINTS = ("is effective", "increases", "improves", "reduces")
    NEGATIVE_CLAIM_HINTS = ("is not effective", "does not increase", "does not improve", "worsens")

    def filter_sources(self, sources: list[dict[str, str]]) -> list[dict[str, str | float]]:
        validated: list[dict[str, str | float]] = []
        for source in sources:
            content = source.get("content", "")
            url = source.get("url", "")
            if len(content) < 100 or not url.startswith("http"):
                continue
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

    def detect_contradictions(self, sources: list[dict[str, str | float]]) -> list[dict[str, str | int]]:
        contradictions: list[dict[str, str | int]] = []
        for left_idx, left_source in enumerate(sources):
            left_content = str(left_source.get("content", "")).lower()
            for right_idx in range(left_idx + 1, len(sources)):
                right_source = sources[right_idx]
                right_content = str(right_source.get("content", "")).lower()
                has_positive_left = any(term in left_content for term in self.POSITIVE_CLAIM_HINTS)
                has_negative_left = any(term in left_content for term in self.NEGATIVE_CLAIM_HINTS)
                has_positive_right = any(term in right_content for term in self.POSITIVE_CLAIM_HINTS)
                has_negative_right = any(term in right_content for term in self.NEGATIVE_CLAIM_HINTS)
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
        if not findings:
            return 0.0
        supported = sum(1 for finding in findings if finding.get("support"))
        return round(supported / len(findings), 3)

    def _host(self, url: str) -> str:
        return (urlparse(url).hostname or "").lower()
