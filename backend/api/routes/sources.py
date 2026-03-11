"""GET /sources/sentiment — avg sentiment per source."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from db.database import get_supabase

router = APIRouter()


@router.get("/sentiment")
def get_source_sentiment(
    limit: int = Query(10, description="Top N sources by volume"),
    days: int = Query(7, description="Number of days to look back"),
):
    sb = get_supabase()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = sb.rpc("rpc_source_sentiment", {
        "p_since": since.isoformat(),
        "p_limit": limit,
    }).execute()

    sources = []
    for r in result.data:
        avg = round(float(r["avg_sentiment"] or 0), 4)
        if avg >= 0.6:
            label = "positive"
        elif avg <= 0.4:
            label = "negative"
        else:
            label = "neutral"

        sources.append({
            "source_name": r["source_name"],
            "article_count": r["article_count"],
            "avg_sentiment": avg,
            "sentiment_label": label,
        })

    return {"sources": sources}
