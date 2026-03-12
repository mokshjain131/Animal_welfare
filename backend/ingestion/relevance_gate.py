"""Filter articles for animal welfare relevance using weighted keyword scoring.

Scoring:
  • keyword found in the **title**     → +2 points
  • keyword found in the body only     → +1 point
  • minimum threshold to pass the gate → 2 points

This means one title keyword is enough, but a single incidental mention
buried in the body text is not.
"""

import logging

from config.keywords import get_all_keywords

logger = logging.getLogger(__name__)

# Minimum score an article needs to pass the relevance gate.
_MIN_SCORE = 2


def relevance_score(article: dict) -> tuple[int, list[str]]:
    """Compute a relevance score for an article.

    Returns (score, matched_keywords) so callers can inspect why an article
    was accepted/rejected.
    """
    title = (article.get("title") or "").lower()
    full_text = (article.get("full_text") or "").lower()

    score = 0
    matched: list[str] = []

    for keyword in get_all_keywords():
        if keyword in title:
            score += 2
            matched.append(f"{keyword} [title]")
        elif keyword in full_text:
            score += 1
            matched.append(f"{keyword} [body]")

    return score, matched


def is_relevant(article: dict) -> bool:
    """Check if an article scores above the relevance threshold.

    Input : article — dict with 'title' and 'full_text' keys
    Output: True if score >= _MIN_SCORE, False otherwise
    """
    score, matched = relevance_score(article)

    if score >= _MIN_SCORE:
        logger.debug(
            "PASS (score=%d): %s — %s",
            score, (article.get("title") or "")[:60], ", ".join(matched[:5]),
        )
        return True

    if matched:
        logger.debug(
            "REJECT (score=%d, needed %d): %s — %s",
            score, _MIN_SCORE, (article.get("title") or "")[:60], ", ".join(matched),
        )
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
