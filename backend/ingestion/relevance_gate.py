"""Filter articles for animal welfare relevance using keyword matching."""

import logging
import re

from config.keywords import get_all_keywords

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for each keyword.
# Use word-boundary matching (\b) to avoid false positives
# like "million" matching "lion" or "knowledge" matching "owl".
_KEYWORD_PATTERNS: list[re.Pattern] = []


def _ensure_patterns() -> list[re.Pattern]:
    """Lazily compile keyword patterns on first use."""
    if not _KEYWORD_PATTERNS:
        for kw in get_all_keywords():
            # Escape to handle special regex chars in keywords (e.g. hyphens)
            pattern = r"\b" + re.escape(kw) + r"\b"
            _KEYWORD_PATTERNS.append(re.compile(pattern, re.IGNORECASE))
    return _KEYWORD_PATTERNS


def is_relevant(article: dict) -> bool:
    """Check if an article contains any animal welfare keyword (word-boundary aware).

    Input : article — dict with 'title' and 'full_text' keys
    Output: True if at least one keyword found, False otherwise
    """
    text = (article.get("title", "") + " " + article.get("full_text", "")).lower()

    for pattern in _ensure_patterns():
        if pattern.search(text):
            return True

    return False


def filter_relevant(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split articles into relevant and rejected groups.

    Input : articles — list of normalized article dicts
    Output: (relevant_articles, rejected_articles)
    """
    relevant = []
    rejected = []

    for article in articles:
        if is_relevant(article):
            relevant.append(article)
        else:
            rejected.append(article)

    logger.info(
        "Relevance gate: %d relevant, %d rejected", len(relevant), len(rejected)
    )
    return relevant, rejected
