"""Remove duplicate articles by checking URLs against the database."""

import logging

from supabase import Client

logger = logging.getLogger(__name__)


def get_existing_urls(sb: Client) -> set[str]:
    """Fetch all article URLs from the database for O(1) lookup.

    Input : sb — Supabase client
    Output: set of URL strings already stored in the articles table
    """
    result = sb.table("articles").select("url").execute()
    return {row["url"] for row in result.data}


def deduplicate(articles: list[dict], sb: Client) -> list[dict]:
    """Remove articles whose URLs already exist in DB or appear twice in the batch.

    Input : articles — list of normalized article dicts (must have 'url' key)
            sb — Supabase client
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
