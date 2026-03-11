"""GET /topics/volume — article count per topic."""

from datetime import date, timedelta

from fastapi import APIRouter, Query

from db.database import get_supabase

router = APIRouter()


@router.get("/volume")
def get_topics_volume(
    days: int = Query(7, description="Number of days to aggregate"),
):
    sb = get_supabase()
    since = date.today() - timedelta(days=days)

    result = sb.rpc("rpc_topic_volumes", {"p_since": str(since)}).execute()

    return {
        "data": [
            {"topic": row["topic"], "article_count": row["article_count"]}
            for row in result.data
        ]
    }
