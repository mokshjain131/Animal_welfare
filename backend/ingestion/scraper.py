"""Extract full article text from URLs using trafilatura."""

import logging
import time

import trafilatura

from config.settings import settings

logger = logging.getLogger(__name__)


def scrape_full_text(url: str) -> str | None:
    """Download a page and extract the main article text.

    Input : url — article URL to scrape
    Output: extracted text string, or None if extraction failed or text too short
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            logger.debug("Trafilatura could not download: %s", url)
            return None

        text = trafilatura.extract(downloaded)
        if text is None:
            logger.debug("Trafilatura could not extract text: %s", url)
            return None

        if len(text) < settings.FALLBACK_TEXT_LENGTH:
            logger.debug("Extracted text too short (%d chars): %s", len(text), url)
            return None

        return text

    except Exception as e:
        logger.error("Scraping error for %s: %s", url, e)
        return None


def enrich_with_full_text(articles: list[dict]) -> list[dict]:
    """Add full_text to each article; fall back to title + description if scraping fails.

    Input : articles — list of article dicts (must have 'url', 'title', 'description')
    Output: same list with 'full_text' key added to every article
    """
    for i, article in enumerate(articles):
        text = scrape_full_text(article["url"])

        if text is not None:
            article["full_text"] = text
        else:
            fallback = article.get("title", "") + ". " + article.get("description", "")
            article["full_text"] = fallback.strip()

        # Rate-limit: 1 second between requests to avoid bans
        if i < len(articles) - 1:
            time.sleep(1)

    scraped_count = sum(1 for a in articles if len(a.get("full_text", "")) > settings.FALLBACK_TEXT_LENGTH)
    logger.info("Scraped full text for %d / %d articles", scraped_count, len(articles))
    return articles
