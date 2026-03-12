"""Extract full article text from URLs using trafilatura."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import trafilatura
from trafilatura.settings import use_config as traf_use_config

from config.settings import settings

logger = logging.getLogger(__name__)

# Configure trafilatura with a shorter download timeout
_TRAF_CONFIG = traf_use_config()
_TRAF_CONFIG.set("DEFAULT", "DOWNLOAD_TIMEOUT", "10")

# Hard per-URL timeout in seconds — kills the thread if trafilatura hangs
_URL_TIMEOUT = 20


def _fetch_and_extract(url: str) -> str | None:
    """Inner function that runs inside a thread with a hard timeout."""
    downloaded = trafilatura.fetch_url(url, config=_TRAF_CONFIG)
    if downloaded is None:
        return None
    return trafilatura.extract(downloaded)


def scrape_full_text(url: str) -> str | None:
    """Download a page and extract the main article text.

    Input : url — article URL to scrape
    Output: extracted text string, or None if extraction failed or text too short
    """
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch_and_extract, url)
            text = future.result(timeout=_URL_TIMEOUT)

        if text is None:
            logger.debug("Trafilatura could not extract text: %s", url)
            return None

        if len(text) < settings.FALLBACK_TEXT_LENGTH:
            logger.debug("Extracted text too short (%d chars): %s", len(text), url)
            return None

        return text

    except FuturesTimeout:
        logger.warning("Scraping timed out after %ds: %s", _URL_TIMEOUT, url)
        return None
    except Exception as e:
        logger.error("Scraping error for %s: %s", url, e)
        return None


# Domains to skip scraping (e.g. paywalled sites that always return 403)
_SKIP_SCRAPE_DOMAINS = ("nytimes.com",)


def enrich_with_full_text(articles: list[dict]) -> list[dict]:
    """Add full_text to each article; fall back to title + description if scraping fails.

    Input : articles — list of article dicts (must have 'url', 'title', 'description')
    Output: same list with 'full_text' key added to every article
    """
    for i, article in enumerate(articles):
        url = article["url"]

        # Skip scraping for blocked/paywalled domains
        if any(domain in url for domain in _SKIP_SCRAPE_DOMAINS):
            fallback = article.get("title", "") + ". " + article.get("description", "")
            article["full_text"] = fallback.strip()
            logger.debug("Skipped scraping (blocked domain): %s", url)
            continue

        text = scrape_full_text(url)

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
