"""Spike detector — flags topics with unusual article volume."""

import logging
from datetime import date, timedelta

from supabase import Client

from config.keywords import get_topic_labels
from config.settings import settings

logger = logging.getLogger(__name__)


def compute_weekly_average(topic: str, sb: Client) -> float:
    """Average daily article count for `topic` over the past 7 days."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    result = (
        sb.table("daily_summaries")
        .select("article_count")
        .eq("topic", topic)
        .gte("date", str(week_ago))
        .lt("date", str(today))
        .execute()
    )

    total = sum(row["article_count"] for row in result.data)
    return total / 7


def detect_spikes(sb: Client) -> list[dict]:
    """Check each topic for a spike in today's article count.

    Creates spike_events for new spikes, resolves events that have subsided.
    Returns list of newly detected spikes.
    """
    today = date.today()
    new_spikes: list[dict] = []

    for topic_label in get_topic_labels():
        # Get today's article count from daily_summaries
        result = (
            sb.table("daily_summaries")
            .select("article_count")
            .eq("topic", topic_label)
            .eq("date", str(today))
            .limit(1)
            .execute()
        )
        today_count = result.data[0]["article_count"] if result.data else 0

        weekly_avg = compute_weekly_average(topic_label, sb)
        multiplier = today_count / max(weekly_avg, 1)

        if multiplier >= settings.SPIKE_MULTIPLIER:
            # Check if spike already recorded for today
            existing = (
                sb.table("spike_events")
                .select("id")
                .eq("topic", topic_label)
                .eq("spike_date", str(today))
                .limit(1)
                .execute()
            )
            if not existing.data:
                sb.table("spike_events").insert({
                    "topic": topic_label,
                    "spike_date": str(today),
                    "article_count": today_count,
                    "weekly_avg": round(weekly_avg, 4),
                    "multiplier": round(multiplier, 4),
                    "is_active": True,
                }).execute()
                new_spikes.append({
                    "topic": topic_label,
                    "today_count": today_count,
                    "weekly_avg": round(weekly_avg, 4),
                    "multiplier": round(multiplier, 4),
                })
                logger.warning(
                    "SPIKE detected: %s — %d articles today (%.1f× avg)",
                    topic_label, today_count, multiplier,
                )
        else:
            # Resolve any active spike for this topic
            sb.table("spike_events").update(
                {"is_active": False}
            ).eq("topic", topic_label).eq("is_active", True).execute()

    return new_spikes


def run_aggregator(sb: Client) -> None:
    """Run all three aggregator jobs in sequence."""
    from aggregator.daily_summary import compute_daily_summaries
    from aggregator.tfidf_keywords import compute_trending_keywords

    logger.info("Aggregator: starting")

    compute_daily_summaries(sb)
    compute_trending_keywords(sb)
    spikes = detect_spikes(sb)

    if spikes:
        logger.info("Aggregator: %d new spike(s) detected", len(spikes))
    else:
        logger.info("Aggregator: no new spikes")

    logger.info("Aggregator: complete")
