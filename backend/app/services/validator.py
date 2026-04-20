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
        if not findings:
            return 0.0
        supported = sum(1 for finding in findings if finding.get("support"))
        return round(supported / len(findings), 3)

    def _host(self, url: str) -> str:
        return (urlparse(url).hostname or "").lower()
