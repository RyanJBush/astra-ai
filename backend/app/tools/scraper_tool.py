import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScraperTool:
    """Downloads a page and extracts normalized text content."""

    async def extract(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "AstraAIResearchBot/0.1"})
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = " ".join(soup.get_text(" ").split())
        logger.info("scraper.completed", extra={"url": url, "chars": len(text)})
        return text[:10000]
