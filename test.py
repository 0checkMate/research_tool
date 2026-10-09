
from app.config import validate_settings
from app.search import search_web
from app.scraper import scrape_pages

validate_settings()

# # This script tests the search_web function from the app.search module.
# for result in search_web('latest developments in LangChain'):
#     print(result.score, '|', result.title)
#     print('   ', result.url)


# This script tests the scrape_pages function from the app.scraper module.
results = search_web('latest developments in LangChain')
pages = scrape_pages(results)

for page in pages:
    status = 'OK' if page.ok else 'FAILED: ' + page.error
    print(status, '|', page.title)
    print('   ', page.url)
    print('   ', len(page.text), 'characters')
    print('   ', page.text[:150])