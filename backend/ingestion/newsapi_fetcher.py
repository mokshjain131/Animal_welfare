"""Fetch articles from NewsAPI using plain requests."""

import logging
from datetime import datetime, timezone

import requests

from config.settings import settings
from config.keywords import TOPIC_KEYWORDS

logger = logging.getLogger(__name__)

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


def fetch_newsapi_articles(query: str, page_size: int = 20) -> list[dict]:
    """Call NewsAPI with a keyword query and return matching articles.

    Input : query — search string, e.g. "factory farm OR battery cage"
            page_size — max results per request (default 20)
    Output: list of dicts with keys: title, url, description, source_name, published_at
    """
    if not settings.NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY is empty — skipping NewsAPI fetch")
        return []

    try:
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": settings.NEWSAPI_KEY,
        }
        resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=15)
        data = resp.json()

        if data.get("status") != "ok":
            logger.error("NewsAPI error: %s", data.get("message", "unknown"))
            return []

        articles = []
        for item in data.get("articles", []):
            url = item.get("url", "")
            if not url:
                continue

            # Parse published date
            published_at = datetime.now(timezone.utc)
            raw_date = item.get("publishedAt", "")
            if raw_date:
                try:
                    published_at = datetime.fromisoformat(
                        raw_date.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            source_name = ""
            if item.get("source") and item["source"].get("name"):
                source_name = item["source"]["name"]

            articles.append({
                "title": (item.get("title") or "").strip(),
                "url": url.strip(),
                "description": (item.get("description") or "").strip(),
                "source_name": source_name,
                "published_at": published_at,
            })

        logger.info("NewsAPI returned %d articles for query: %s", len(articles), query[:60])
        return articles

    except requests.RequestException as e:
        logger.error("NewsAPI request failed: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected NewsAPI error: %s", e)
        return []


def fetch_all_newsapi_articles() -> list[dict]:
    """Run NewsAPI queries for each topic using its first 3 keywords.

    Input : None (reads TOPIC_KEYWORDS and settings.NEWSAPI_KEY)
    Output: combined list of article dicts from all topic queries
    """
    if not settings.NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY is empty — skipping all NewsAPI fetches")
        return []

    all_articles = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        query = " OR ".join(keywords[:3])
        articles = fetch_newsapi_articles(query)
        all_articles.extend(articles)
        logger.info("NewsAPI topic '%s': %d articles", topic, len(articles))

    logger.info("Total NewsAPI articles fetched: %d", len(all_articles))
    return all_articles
