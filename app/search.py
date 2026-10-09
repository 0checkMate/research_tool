from tavily import TavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib.parse import urldefrag

from app.config import TAVILY_API_KEY
from app.schemas import SearchResult

client = TavilyClient(api_key=TAVILY_API_KEY)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
def search_web(query: str, max_results: int = 5) -> list[SearchResult]:
    response = client.search(query=query, max_results=max_results)
    results = [
        SearchResult(
            title=item.get('title', ''),
            url=item['url'],
            snippet=item.get('content', ''),
            score=item.get('score', 0.0),
        )
        for item in response.get('results', [])
    ]
    seen = set()
    unique = []
    for result in results:
        key = urldefrag(result.url).url
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique