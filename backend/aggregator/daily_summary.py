"""Daily summary aggregator — computes per-topic sentiment rollups."""

import logging
from datetime import date, datetime, timedelta, timezone

from supabase import Client

from config.keywords import get_topic_labels

logger = logging.getLogger(__name__)


def _compute_summary_for_date(target_date: date, sb: Client) -> int:
    """Compute per-topic sentiment aggregates for a single date.

    Returns the number of summary rows upserted.
    """
    start_dt = datetime(target_date.year, target_date.month, target_date.day,
                        tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)

    rows_written = 0

    for topic_label in get_topic_labels():
        # Call the RPC function for aggregate stats
        result = sb.rpc("rpc_daily_summary_stats", {
            "p_topic": topic_label,
            "p_start": start_dt.isoformat(),
            "p_end": end_dt.isoformat(),
        }).execute()

        row = result.data[0] if result.data else None
        total = int(row["total"] or 0) if row else 0
        if total == 0:
            continue

        avg_sentiment = round(float(row["avg_score"] or 0), 4)
        pos_count = int(row["pos"] or 0)
        neg_count = int(row["neg"] or 0)
        neu_count = int(row["neu"] or 0)

        # Upsert using UNIQUE(date, topic) constraint
        sb.table("daily_summaries").upsert({
            "date": str(target_date),
            "topic": topic_label,
            "article_count": total,
            "avg_sentiment": avg_sentiment,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
        }, on_conflict="date,topic").execute()
        rows_written += 1

    return rows_written


def compute_daily_summaries(sb: Client, lookback_days: int = 3) -> None:
    """Compute per-topic sentiment aggregates for the last `lookback_days` days.

    Using a lookback window (default 3 days) instead of just today ensures
    that summaries are never permanently missed due to downtime, migrations,
    or late-arriving articles.
    """
    today = date.today()
    total_rows = 0

    for i in range(lookback_days, -1, -1):  # oldest first
        target = today - timedelta(days=i)
        rows = _compute_summary_for_date(target, sb)
        total_rows += rows

    logger.info(
        "Daily summaries: %d total rows written for %s to %s",
        total_rows,
        today - timedelta(days=lookback_days),
        today,
    )


def compute_historical_summaries(sb: Client, days_back: int = 30) -> None:
    """Backfill daily summaries for past N days."""
    today = date.today()
    total_rows = 0

    for i in range(days_back, -1, -1):  # oldest first
        target = today - timedelta(days=i)
        rows = _compute_summary_for_date(target, sb)
        total_rows += rows

    logger.info(
        "Historical summaries: %d total rows written for %d days",
        total_rows, days_back + 1,
    )
