# news_engine.py
# FIXED: uses env-variable key, clean query string, graceful fallback
import os
import requests
from config import NEWS_API_KEY


def get_latest_news(stock: str, max_articles: int = 6) -> list[dict]:
    """
    Fetch recent news for a stock symbol.
    Returns list of dicts: {title, description, url, publishedAt, sentiment_hint}
    Falls back to empty list if API key missing or request fails.
    """
    # Strip exchange suffix: RELIANCE.NS → RELIANCE
    query = stock.split(".")[0].upper()

    key = NEWS_API_KEY or os.getenv("NEWS_API_KEY", "")
    if not key or key == "your_newsapi_key_here":
        print("[news_engine] NEWS_API_KEY not set — news skipped")
        return _fallback_news(query)

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        f"{query} stock",
                "language": "en",
                "sortBy":   "publishedAt",
                "pageSize": max_articles,
                "apiKey":   key,
            },
            timeout=8,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title":        a.get("title", ""),
                "description":  a.get("description", ""),
                "url":          a.get("url", ""),
                "publishedAt":  a.get("publishedAt", ""),
            }
            for a in articles if a.get("title")
        ]
    except Exception as e:
        print(f"[news_engine] Request failed: {e}")
        return _fallback_news(query)


def _fallback_news(query: str) -> list[dict]:
    """Return placeholder headlines when API is unavailable."""
    return [
        {"title": f"{query}: No live news (set NEWS_API_KEY in .env)",
         "description": "Add your NewsAPI key to get real headlines.",
         "url": "https://newsapi.org",
         "publishedAt": ""},
    ]


def get_news_titles(stock: str) -> list[str]:
    """Convenience wrapper — returns just the title strings."""
    return [n["title"] for n in get_latest_news(stock)]