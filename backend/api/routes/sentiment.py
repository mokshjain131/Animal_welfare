"""GET /sentiment/trend — daily avg sentiment over time."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from db.database import get_supabase

router = APIRouter()


@router.get("/trend")
def get_sentiment_trend(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    days: int = Query(7, description="Number of days to return"),
):
    sb = get_supabase()
    since = date.today() - timedelta(days=days)

    query = (
        sb.table("daily_summaries")
        .select("date, avg_sentiment, article_count, topic")
        .gte("date", str(since))
    )

    if topic:
        query = query.eq("topic", topic)

    result = query.order("date", desc=False).order("topic", desc=False).execute()

    return {
        "data": [
            {
                "date": row["date"],
                "avg_sentiment": row["avg_sentiment"],
                "article_count": row["article_count"],
                "topic": row["topic"],
            }
            for row in result.data
        ]
    }
