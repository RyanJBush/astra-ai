import logging
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Simple web search adapter using DuckDuckGo HTML results."""

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers={"User-Agent": "AstraAIResearchBot/0.1"})
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []

        for result in soup.select(".result"):
            anchor = result.select_one(".result__a")
            snippet = result.select_one(".result__snippet")
            if not anchor:
                continue

            results.append(
                {
                    "title": anchor.get_text(strip=True),
                    "url": anchor.get("href", ""),
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                }
            )
            if len(results) >= max_results:
                break

        logger.info("web_search.completed", extra={"query": query, "results": len(results)})
        return results
