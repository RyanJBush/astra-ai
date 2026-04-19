from urllib.parse import quote_plus

import requests


class SearchTool:
    def search(self, query: str) -> list[str]:
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&format=json&search={quote_plus(query)}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        links = payload[3] if isinstance(payload, list) and len(payload) > 3 else []
        return links[:3]
