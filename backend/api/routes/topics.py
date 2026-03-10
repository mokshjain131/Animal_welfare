"""GET /topics/volume — article count per topic."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import DailySummary

router = APIRouter()


@router.get("/volume")
def get_topics_volume(
    days: int = Query(7, description="Number of days to aggregate"),
    db: Session = Depends(get_db),
):
    since = date.today() - timedelta(days=days)

    rows = (
        db.query(
            DailySummary.topic,
            func.sum(DailySummary.article_count).label("article_count"),
        )
        .filter(DailySummary.date >= since)
        .group_by(DailySummary.topic)
        .order_by(func.sum(DailySummary.article_count).desc())
        .all()
    )

    return {
        "data": [
            {"topic": row.topic, "article_count": row.article_count}
            for row in rows
        ]
    }
