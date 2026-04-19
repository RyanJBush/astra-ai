import requests
from bs4 import BeautifulSoup


class Scraper:
    def extract(self, url: str) -> tuple[str, str]:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = (soup.title.string.strip() if soup.title and soup.title.string else url)[:500]
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        content = " ".join(p for p in paragraphs if p)
        return title, content[:5000]
