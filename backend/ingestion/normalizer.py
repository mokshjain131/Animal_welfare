"""Normalize raw articles from any source into a standard schema."""

import logging
from datetime import datetime, timezone

from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


def normalize_article(raw: dict, source_type: str) -> dict | None:
    """Convert a raw article dict into the standard article schema.

    Input : raw — dict from RSS or NewsAPI fetcher
            source_type — "rss" or "newsapi"
    Output: normalized dict with keys: title, full_text, source_name, url, published_at, source_type
            or None if the article is invalid (missing url)
    """
    url = (raw.get("url") or "").strip()
    if not url or not url.startswith("http"):
        logger.debug("Skipping article with invalid URL: %s", url)
        return None

    title = (raw.get("title") or "").strip()[:1000]
    full_text = (raw.get("full_text") or "").strip()
    source_name = (raw.get("source_name") or "unknown").strip()

    # Parse published_at — accept datetime objects or strings
    published_at = raw.get("published_at")
    if isinstance(published_at, str):
        try:
            published_at = dateutil_parser.parse(published_at)
        except (ValueError, TypeError):
            published_at = datetime.now(timezone.utc)
    elif not isinstance(published_at, datetime):
        published_at = datetime.now(timezone.utc)

    # Ensure timezone-aware
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    return {
        "title": title,
        "full_text": full_text,
        "source_name": source_name,
        "url": url,
        "published_at": published_at,
        "source_type": source_type,
    }


def normalize_all(rss_articles: list[dict], newsapi_articles: list[dict]) -> list[dict]:
    """Normalize and merge articles from all sources into one list.

    Input : rss_articles — raw dicts from RSS fetcher
            newsapi_articles — raw dicts from NewsAPI fetcher
    Output: list of normalized article dicts (invalid articles filtered out)
    """
    normalized = []

    for raw in rss_articles:
        article = normalize_article(raw, source_type="rss")
        if article:
            normalized.append(article)

    for raw in newsapi_articles:
        article = normalize_article(raw, source_type="newsapi")
        if article:
            normalized.append(article)

    logger.info(
        "Normalized %d articles (RSS: %d, NewsAPI: %d)",
        len(normalized), len(rss_articles), len(newsapi_articles),
    )
    return normalized
