# Scraper for fetching data from the web

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from app.schemas import ScrapedPage, SearchResult

USER_AGENT = 'MultiAgentSearchBot/0.1 (learning project)'
TIMEOUT_SECONDS = 10
MAX_CHARS = 6000
MAX_WORKERS = 5
REMOVE_TAGS = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript']


def allowed_by_robots(url: str) -> bool:
    parts = urlparse(url)
    robots_url = f'{parts.scheme}://{parts.netloc}/robots.txt'
    try:
        response = requests.get(robots_url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        return False
    if 400 <= response.status_code < 500:
        return True
    if response.status_code != 200:
        return False
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser.can_fetch(USER_AGENT, url)


def scrape_page(result: SearchResult) -> ScrapedPage:
    url = result.url
    try:
        if not allowed_by_robots(url):
            return ScrapedPage(url=url, title=result.title, text=result.snippet, ok=False, error='Blocked by robots.txt')

        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        if 'text/html' not in response.headers.get('Content-Type', ''):
            return ScrapedPage(url=url, title=result.title, text=result.snippet, ok=False, error='Not an HTML page')

        soup = BeautifulSoup(response.text, 'lxml')
        for tag in soup(REMOVE_TAGS):
            tag.decompose()

        title = soup.title.get_text(strip=True) if soup.title else result.title
        container = soup.find('article') or soup.find('main') or soup.body or soup
        text = ' '.join(container.get_text(separator=' ').split())
        return ScrapedPage(url=url, title=title, text=text[:MAX_CHARS])

    except requests.RequestException as error:
        return ScrapedPage(url=url, title=result.title, text=result.snippet, ok=False, error=str(error))


def scrape_pages(results: list[SearchResult]) -> list[ScrapedPage]:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        return list(executor.map(scrape_page, results))