"""GET /overview/metrics — dashboard stat cards."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import (
    Article, DailySummary, FlaggedArticle, SentimentScore, SpikeEvent,
)

router = APIRouter()


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    today = date.today()
    yesterday = today - timedelta(days=1)

    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    yesterday_start = today_start - timedelta(days=1)

    # Articles today
    articles_today = (
        db.query(func.count(Article.id))
        .filter(Article.published_at >= today_start)
        .scalar()
    ) or 0

    # Avg sentiment today
    avg_sentiment_today = (
        db.query(func.avg(SentimentScore.score))
        .join(Article, Article.id == SentimentScore.article_id)
        .filter(Article.published_at >= today_start)
        .scalar()
    )

    # Avg sentiment yesterday (for comparison)
    avg_sentiment_yesterday = (
        db.query(func.avg(SentimentScore.score))
        .join(Article, Article.id == SentimentScore.article_id)
        .filter(
            Article.published_at >= yesterday_start,
            Article.published_at < today_start,
        )
        .scalar()
    )

    avg_sent = round(float(avg_sentiment_today or 0), 4)
    avg_sent_yest = float(avg_sentiment_yesterday or 0)
    avg_sent_vs = round(avg_sent - avg_sent_yest, 4) if avg_sentiment_yesterday else 0.0

    # Determine label
    if avg_sent >= 0.6:
        label = "positive"
    elif avg_sent <= 0.4:
        label = "negative"
    else:
        label = "neutral"

    # Active topics (topics with articles in last 7 days)
    week_ago = today_start - timedelta(days=7)
    active_topics = (
        db.query(func.count(func.distinct(DailySummary.topic)))
        .filter(DailySummary.date >= today - timedelta(days=7))
        .scalar()
    ) or 0

    # Misinfo alerts (unreviewed flagged articles)
    misinfo_alerts = (
        db.query(func.count(FlaggedArticle.id))
        .filter(FlaggedArticle.is_reviewed == False)
        .scalar()
    ) or 0

    # Active spike
    active_spike = (
        db.query(SpikeEvent)
        .filter(SpikeEvent.is_active == True)
        .order_by(SpikeEvent.detected_at.desc())
        .first()
    )

    spike_data = None
    if active_spike:
        spike_data = {
            "topic": active_spike.topic,
            "multiplier": active_spike.multiplier,
            "detected_at": active_spike.detected_at.isoformat() if active_spike.detected_at else None,
        }

    return {
        "articles_today": articles_today,
        "avg_sentiment": avg_sent,
        "avg_sentiment_label": label,
        "avg_sentiment_vs_yesterday": avg_sent_vs,
        "active_topics": active_topics,
        "misinfo_alerts": misinfo_alerts,
        "active_spike": spike_data,
    }
