"""Pipeline orchestration and scheduler setup."""

import logging
import traceback
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings

logger = logging.getLogger(__name__)

# Track run count so we can skip NewsAPI on odd runs (conserve quota)
_run_count = 0


def run_ingestion_pipeline() -> None:
    """Execute the complete ingestion → NLP → aggregation pipeline."""
    global _run_count
    _run_count += 1

    start = datetime.now(timezone.utc)
    logger.info("Pipeline run #%d started at %s", _run_count, start.isoformat())

    try:
        # ── Lazy imports to avoid circular deps / heavy model loads at import ──
        from ingestion.rss_fetcher import fetch_all_rss_feeds
        from ingestion.newsapi_fetcher import fetch_all_newsapi_articles
        from ingestion.scraper import enrich_with_full_text
        from ingestion.normalizer import normalize_all
        from ingestion.deduplicator import deduplicate
        from ingestion.relevance_gate import filter_relevant
        from nlp.pipeline import process_unprocessed_articles
        from aggregator.spike_detector import run_aggregator
        from db.database import get_supabase

        sb = get_supabase()

        try:
            # 1. Fetch RSS
            articles_rss = fetch_all_rss_feeds()
            logger.info("Fetched %d RSS articles", len(articles_rss))

            # 2. Fetch NewsAPI (every run)
            articles_newsapi = fetch_all_newsapi_articles()
            logger.info("Fetched %d NewsAPI articles", len(articles_newsapi))

            # 3. Enrich with full text (each set separately to preserve source info)
            enriched_rss = enrich_with_full_text(articles_rss)
            enriched_newsapi = enrich_with_full_text(articles_newsapi)

            # 4. Normalize
            normalized = normalize_all(enriched_rss, enriched_newsapi)
            logger.info("Normalized %d articles", len(normalized))

            # 5. Deduplicate against database
            unique = deduplicate(normalized, sb)
            logger.info("After dedup: %d unique articles", len(unique))

            # 6. Filter for relevance
            relevant, rejected = filter_relevant(unique)
            logger.info(
                "Relevance filter: %d relevant, %d rejected",
                len(relevant), len(rejected),
            )

            # 7. Save new articles to Supabase
            saved = 0
            if relevant:
                rows_to_insert = []
                for article_data in relevant:
                    rows_to_insert.append({
                        "url": article_data["url"],
                        "title": article_data["title"],
                        "full_text": article_data.get("full_text"),
                        "source_name": article_data["source_name"],
                        "source_type": article_data["source_type"],
                        "published_at": article_data["published_at"].isoformat()
                            if hasattr(article_data["published_at"], "isoformat")
                            else str(article_data["published_at"]),
                        "is_processed": False,
                    })

                # Try batch upsert first; fall back to one-by-one on error
                # (handles auto-increment sequence mismatches after migration)
                try:
                    sb.table("articles").upsert(
                        rows_to_insert,
                        on_conflict="url",
                        ignore_duplicates=True,
                    ).execute()
                    saved = len(rows_to_insert)
                except Exception as batch_err:
                    logger.warning(
                        "Batch insert failed (%s), falling back to individual inserts",
                        batch_err,
                    )
                    for row in rows_to_insert:
                        try:
                            sb.table("articles").upsert(
                                row,
                                on_conflict="url",
                                ignore_duplicates=True,
                            ).execute()
                            saved += 1
                        except Exception:
                            pass  # skip rows that still fail (e.g. sequence clash)
            logger.info("Saved %d new articles to database", saved)

            # 8. Run NLP on unprocessed articles
            processed = process_unprocessed_articles(sb)
            logger.info("NLP processed %d articles", processed)

            # 9. Run aggregator
            run_aggregator(sb)

            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info(
                "Pipeline run #%d complete in %.1fs — "
                "fetched=%d, saved=%d, processed=%d, rejected=%d",
                _run_count, elapsed,
                len(articles_rss) + len(articles_newsapi),
                saved, processed, len(rejected),
            )

        finally:
            pass  # Supabase client doesn't need explicit close

    except Exception:
        logger.error(
            "Pipeline run #%d FAILED:\n%s", _run_count, traceback.format_exc()
        )


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=run_ingestion_pipeline,
        trigger=IntervalTrigger(minutes=settings.PIPELINE_INTERVAL_MINUTES),
        id="ingestion_pipeline",
        replace_existing=True,
    )
    logger.info(
        "Scheduler configured: pipeline runs every %d minutes",
        settings.PIPELINE_INTERVAL_MINUTES,
    )
    return scheduler
