import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-3.6-flash')


def validate_settings():
    required = {
        'GOOGLE_API_KEY': GOOGLE_API_KEY,
        'TAVILY_API_KEY': TAVILY_API_KEY,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError('Missing required environment variables: ' + ', '.join(missing))