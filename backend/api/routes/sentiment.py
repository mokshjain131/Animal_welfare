"""GET /sentiment/trend — daily avg sentiment over time."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import DailySummary

router = APIRouter()


@router.get("/trend")
def get_sentiment_trend(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    days: int = Query(7, description="Number of days to return"),
    db: Session = Depends(get_db),
):
    since = date.today() - timedelta(days=days)

    query = db.query(DailySummary).filter(DailySummary.date >= since)

    if topic:
        query = query.filter(DailySummary.topic == topic)

    query = query.order_by(DailySummary.date.asc(), DailySummary.topic.asc())
    rows = query.all()

    return {
        "data": [
            {
                "date": str(row.date),
                "avg_sentiment": row.avg_sentiment,
                "article_count": row.article_count,
                "topic": row.topic,
            }
            for row in rows
        ]
    }
