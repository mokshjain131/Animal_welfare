"""Spike detector — flags topics with unusual article volume."""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from config.keywords import get_topic_labels
from config.settings import settings
from db.models import DailySummary, SpikeEvent

logger = logging.getLogger(__name__)


def compute_weekly_average(topic: str, db: Session) -> float:
    """Average daily article count for `topic` over the past 7 days."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    rows = (
        db.query(DailySummary.article_count)
        .filter(
            DailySummary.topic == topic,
            DailySummary.date >= week_ago,
            DailySummary.date < today,  # exclude today
        )
        .all()
    )

    total = sum(row.article_count for row in rows)
    return total / 7


def detect_spikes(db: Session) -> list[dict]:
    """Check each topic for a spike in today's article count.

    Creates spike_events for new spikes, resolves events that have subsided.
    Returns list of newly detected spikes.
    """
    today = date.today()
    new_spikes: list[dict] = []

    for topic_label in get_topic_labels():
        # Get today's article count from daily_summaries
        summary = (
            db.query(DailySummary)
            .filter(
                DailySummary.topic == topic_label,
                DailySummary.date == today,
            )
            .first()
        )
        today_count = summary.article_count if summary else 0

        weekly_avg = compute_weekly_average(topic_label, db)
        multiplier = today_count / max(weekly_avg, 1)

        if multiplier >= settings.SPIKE_MULTIPLIER:
            # Check if spike already recorded for today
            existing = (
                db.query(SpikeEvent)
                .filter(
                    SpikeEvent.topic == topic_label,
                    SpikeEvent.spike_date == today,
                )
                .first()
            )
            if not existing:
                spike = SpikeEvent(
                    topic=topic_label,
                    spike_date=today,
                    article_count=today_count,
                    weekly_avg=round(weekly_avg, 4),
                    multiplier=round(multiplier, 4),
                    is_active=True,
                )
                db.add(spike)
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
            db.query(SpikeEvent).filter(
                SpikeEvent.topic == topic_label,
                SpikeEvent.is_active == True,  # noqa: E712
            ).update({"is_active": False})

    db.commit()
    return new_spikes


def run_aggregator(db: Session) -> None:
    """Run all three aggregator jobs in sequence."""
    from aggregator.daily_summary import compute_daily_summaries
    from aggregator.tfidf_keywords import compute_trending_keywords

    logger.info("Aggregator: starting")

    compute_daily_summaries(db)
    compute_trending_keywords(db)
    spikes = detect_spikes(db)

    if spikes:
        logger.info("Aggregator: %d new spike(s) detected", len(spikes))
    else:
        logger.info("Aggregator: no new spikes")

    logger.info("Aggregator: complete")
