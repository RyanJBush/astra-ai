import re


class SummarizerAgent:
    """Basic summarization with sentence extraction and citation markers."""

    def summarize(self, query: str, source_chunks: list[dict[str, str]]) -> str:
        if not source_chunks:
            return f"No useful sources were found for '{query}'."

        top_lines: list[str] = []
        for idx, chunk in enumerate(source_chunks, start=1):
            sentences = re.split(r"(?<=[.!?])\s+", chunk["content"])
            first_sentence = next((s for s in sentences if len(s) > 60), chunk["snippet"])
            top_lines.append(f"[{idx}] {first_sentence[:280]}")

        return "\n".join(top_lines[:5])
