import re


class PIIRedactor:
    EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
    PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    def redact(self, text: str) -> tuple[str, dict[str, int]]:
        working = str(text or "")
        stats = {"emails": 0, "phones": 0, "ssn": 0, "total": 0}

        def replace_and_count(pattern: re.Pattern, token: str, key: str) -> None:
            nonlocal working
            matches = list(pattern.finditer(working))
            if not matches:
                return
            stats[key] += len(matches)
            working = pattern.sub(token, working)

        replace_and_count(self.EMAIL_RE, "[REDACTED_EMAIL]", "emails")
        replace_and_count(self.PHONE_RE, "[REDACTED_PHONE]", "phones")
        replace_and_count(self.SSN_RE, "[REDACTED_SSN]", "ssn")
        stats["total"] = stats["emails"] + stats["phones"] + stats["ssn"]
        return working, stats
