"""GET /sentiment/trend — daily avg sentiment over time."""

from datetime import date, timedelta
from typing import Optional
from collections import defaultdict

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

    if topic:
        # Single topic — return rows directly
        return {
            "data": [
                {
                    "date": row["date"],
                    "avg_sentiment": round(row["avg_sentiment"], 4),
                    "article_count": row["article_count"],
                    "topic": row["topic"],
                }
                for row in result.data
            ]
        }

    # All topics — aggregate into one data point per day (weighted avg by article_count)
    day_map: dict[str, dict] = defaultdict(lambda: {"total_weighted": 0.0, "total_count": 0})
    for row in result.data:
        d = day_map[row["date"]]
        count = row["article_count"] or 0
        sentiment = row["avg_sentiment"] or 0
        d["total_weighted"] += sentiment * count
        d["total_count"] += count

    data = []
    for dt in sorted(day_map.keys()):
        d = day_map[dt]
        avg = round(d["total_weighted"] / d["total_count"], 4) if d["total_count"] > 0 else 0
        data.append({
            "date": dt,
            "avg_sentiment": avg,
            "article_count": d["total_count"],
            "topic": "all",
        })

    return {"data": data}
