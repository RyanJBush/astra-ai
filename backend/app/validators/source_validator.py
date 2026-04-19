from urllib.parse import urlparse


class SourceValidator:
    TRUSTED_SUFFIXES = (".gov", ".edu", "nature.com", "arxiv.org", "who.int")

    def score(self, url: str, content: str) -> float:
        domain = urlparse(url).netloc.lower()
        domain_score = 0.9 if domain.endswith(self.TRUSTED_SUFFIXES) else 0.55
        length_bonus = min(len(content) / 4000, 0.3)
        return round(min(domain_score + length_bonus, 0.99), 3)
