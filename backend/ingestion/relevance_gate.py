"""Filter articles for animal welfare relevance using keyword matching."""

import logging

from config.keywords import get_all_keywords

logger = logging.getLogger(__name__)


def is_relevant(article: dict) -> bool:
    """Check if an article contains any animal welfare keyword.

    Input : article — dict with 'title' and 'full_text' keys
    Output: True if at least one keyword found, False otherwise
    """
    text = (article.get("title", "") + " " + article.get("full_text", "")).lower()

    for keyword in get_all_keywords():
        if keyword in text:
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
