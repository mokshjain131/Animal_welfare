"""Fetch articles from RSS feeds using feedparser."""

import logging
from datetime import datetime, timezone
from time import mktime

import feedparser

from config.settings import settings

logger = logging.getLogger(__name__)


def fetch_rss_feed(feed_url: str) -> list[dict]:
    """Parse a single RSS feed URL and return raw article dicts.

    Input : feed_url — e.g. "https://feeds.bbci.co.uk/news/rss.xml"
    Output: list of dicts with keys: title, url, description, source_name, published_at
    """
    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            logger.warning("RSS feed failed or empty: %s (%s)", feed_url, feed.bozo_exception)
            return []

        articles = []
        source_name = feed.feed.get("title", feed_url)

        for entry in feed.entries:
            url = entry.get("link", "")
            if not url:
                continue

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime.fromtimestamp(
                    mktime(entry.published_parsed), tz=timezone.utc
                )
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime.fromtimestamp(
                    mktime(entry.updated_parsed), tz=timezone.utc
                )
            else:
                published_at = datetime.now(timezone.utc)

            articles.append({
                "title": entry.get("title", "").strip(),
                "url": url.strip(),
                "description": entry.get("summary", "").strip(),
                "source_name": source_name,
                "published_at": published_at,
            })

        logger.info("Fetched %d articles from RSS: %s", len(articles), source_name)
        return articles

    except Exception as e:
        logger.error("Error fetching RSS feed %s: %s", feed_url, e)
        return []


def fetch_all_rss_feeds() -> list[dict]:
    """Fetch articles from all configured RSS feeds.

    Input : None (reads settings.RSS_FEEDS)
    Output: combined list of raw article dicts from all feeds
    """
    all_articles = []
    for feed_url in settings.RSS_FEEDS:
        articles = fetch_rss_feed(feed_url)
        all_articles.extend(articles)

    logger.info("Total RSS articles fetched: %d", len(all_articles))
    return all_articles
