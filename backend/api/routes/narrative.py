"""GET /narrative/shifts — topic mention volume over time (area chart)."""

from datetime import date, timedelta

from fastapi import APIRouter, Query

from config.keywords import get_topic_labels
from db.database import get_supabase

router = APIRouter()


@router.get("/shifts")
def get_narrative_shifts(
    days: int = Query(14, description="Number of days to return"),
):
    sb = get_supabase()
    since = date.today() - timedelta(days=days)

    result = (
        sb.table("daily_summaries")
        .select("date, topic, article_count")
        .gte("date", str(since))
        .order("date", desc=False)
        .execute()
    )

    # Build date list and per-topic series
    dates_set: set[str] = set()
    topic_map: dict[str, dict[str, int]] = {}

    for row in result.data:
        d = row["date"]
        dates_set.add(d)
        if row["topic"] not in topic_map:
            topic_map[row["topic"]] = {}
        topic_map[row["topic"]][d] = row["article_count"]

    dates = sorted(dates_set)

    series = []
    for topic in get_topic_labels():
        if topic in topic_map:
            values = [topic_map[topic].get(d, 0) for d in dates]
            series.append({"topic": topic, "values": values})

    return {"dates": dates, "series": series}
