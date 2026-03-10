"""Remove duplicate articles by checking URLs against the database."""

import logging

from sqlalchemy.orm import Session

from db.models import Article

logger = logging.getLogger(__name__)


def get_existing_urls(db: Session) -> set[str]:
    """Fetch all article URLs from the database for O(1) lookup.

    Input : db — SQLAlchemy session
    Output: set of URL strings already stored in the articles table
    """
    rows = db.query(Article.url).all()
    return {row[0] for row in rows}


def deduplicate(articles: list[dict], db: Session) -> list[dict]:
    """Remove articles whose URLs already exist in DB or appear twice in the batch.

    Input : articles — list of normalized article dicts (must have 'url' key)
            db — SQLAlchemy session
    Output: filtered list with duplicates removed
    """
    existing_urls = get_existing_urls(db)
    seen_in_batch: set[str] = set()
    unique = []

    for article in articles:
        url = article["url"]
        if url in existing_urls or url in seen_in_batch:
            continue
        seen_in_batch.add(url)
        unique.append(article)

    dropped = len(articles) - len(unique)
    logger.info("Deduplication: %d kept, %d dropped", len(unique), dropped)
    return unique
