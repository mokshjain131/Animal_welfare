"""Remove duplicate articles by checking URLs against the database."""

import logging
from typing import Union

from sqlalchemy.orm import Session
from supabase import Client

logger = logging.getLogger(__name__)

_DBClient = Union[Client, Session]


def get_existing_urls(sb: _DBClient) -> set[str]:
    """Fetch all article URLs from the database for O(1) lookup.

    Input : sb — Supabase client or SQLAlchemy Session
    Output: set of URL strings already stored in the articles table.
            Returns an empty set if the database is unreachable so that
            the pipeline can continue (deduplication falls back to
            within-batch-only checks).
    """
    try:
        if hasattr(sb, "table"):
            # Supabase client
            result = sb.table("articles").select("url").execute()
            return {row["url"] for row in result.data}
        else:
            # SQLAlchemy Session
            from db.models import Article
            rows = sb.query(Article.url).all()
            return {row[0] for row in rows}
    except Exception as exc:
        logger.warning(
            "Could not fetch existing URLs from database (%s). "
            "Deduplication will only check within the current batch.",
            exc,
        )
        return set()


def deduplicate(articles: list[dict], sb: _DBClient) -> list[dict]:
    """Remove articles whose URLs already exist in DB or appear twice in the batch.

    Input : articles — list of normalized article dicts (must have 'url' key)
            sb — Supabase client or SQLAlchemy Session
    Output: filtered list with duplicates removed
    """
    existing_urls = get_existing_urls(sb)
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
