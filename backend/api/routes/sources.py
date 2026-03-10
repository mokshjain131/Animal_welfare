"""GET /sources/sentiment — avg sentiment per source."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Article, SentimentScore

router = APIRouter()


@router.get("/sentiment")
def get_source_sentiment(
    limit: int = Query(10, description="Top N sources by volume"),
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(
            Article.source_name,
            func.count(Article.id).label("article_count"),
            func.avg(SentimentScore.score).label("avg_sentiment"),
        )
        .join(SentimentScore, SentimentScore.article_id == Article.id)
        .filter(Article.published_at >= since)
        .group_by(Article.source_name)
        .order_by(func.count(Article.id).desc())
        .limit(limit)
        .all()
    )

    sources = []
    for r in rows:
        avg = round(float(r.avg_sentiment or 0), 4)
        if avg >= 0.6:
            label = "positive"
        elif avg <= 0.4:
            label = "negative"
        else:
            label = "neutral"

        sources.append({
            "source_name": r.source_name,
            "article_count": r.article_count,
            "avg_sentiment": avg,
            "sentiment_label": label,
        })

    return {"sources": sources}
