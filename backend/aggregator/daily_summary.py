"""Daily summary aggregator — computes per-topic sentiment rollups."""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from config.keywords import get_topic_labels
from db.models import Article, DailySummary, SentimentScore, TopicClassification

logger = logging.getLogger(__name__)


def _compute_summary_for_date(target_date: date, db: Session) -> int:
    """Compute per-topic sentiment aggregates for a single date.

    Returns the number of summary rows upserted.
    """
    start_dt = datetime(target_date.year, target_date.month, target_date.day,
                        tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)

    rows_written = 0

    for topic_label in get_topic_labels():
        # Query articles for this topic on this date
        results = (
            db.query(
                func.count(Article.id).label("total"),
                func.avg(SentimentScore.score).label("avg_score"),
                func.sum(
                    func.cast(SentimentScore.label == "positive", Integer)
                ).label("pos"),
                func.sum(
                    func.cast(SentimentScore.label == "negative", Integer)
                ).label("neg"),
                func.sum(
                    func.cast(SentimentScore.label == "neutral", Integer)
                ).label("neu"),
            )
            .join(TopicClassification, TopicClassification.article_id == Article.id)
            .join(SentimentScore, SentimentScore.article_id == Article.id)
            .filter(
                TopicClassification.topic == topic_label,
                Article.published_at >= start_dt,
                Article.published_at < end_dt,
            )
            .first()
        )

        total = results.total or 0
        if total == 0:
            continue

        avg_sentiment = round(float(results.avg_score or 0), 4)
        pos_count = int(results.pos or 0)
        neg_count = int(results.neg or 0)
        neu_count = int(results.neu or 0)

        # Upsert: delete existing row for this date+topic, then insert
        db.query(DailySummary).filter(
            DailySummary.date == target_date,
            DailySummary.topic == topic_label,
        ).delete()

        summary = DailySummary(
            date=target_date,
            topic=topic_label,
            article_count=total,
            avg_sentiment=avg_sentiment,
            positive_count=pos_count,
            negative_count=neg_count,
            neutral_count=neu_count,
        )
        db.add(summary)
        rows_written += 1

    db.commit()
    return rows_written


def compute_daily_summaries(db: Session) -> None:
    """Compute per-topic sentiment aggregates for today."""
    today = date.today()
    rows = _compute_summary_for_date(today, db)
    logger.info("Daily summaries: %d rows written for %s", rows, today)


def compute_historical_summaries(db: Session, days_back: int = 30) -> None:
    """Backfill daily summaries for past N days."""
    today = date.today()
    total_rows = 0

    for i in range(days_back, -1, -1):  # oldest first
        target = today - timedelta(days=i)
        rows = _compute_summary_for_date(target, db)
        total_rows += rows

    logger.info(
        "Historical summaries: %d total rows written for %d days",
        total_rows, days_back + 1,
    )
