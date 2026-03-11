"""GET /articles/recent and GET /articles/flagged."""

from typing import Optional

from fastapi import APIRouter, Query

from db.database import get_supabase

router = APIRouter()


@router.get("/recent")
def get_recent_articles(
    limit: int = Query(20, description="Max articles to return"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    sentiment: Optional[str] = Query(None, description="Filter: positive, negative, neutral"),
    source: Optional[str] = Query(None, description="Filter by source name"),
):
    sb = get_supabase()
    result = sb.rpc("rpc_recent_articles", {
        "p_topic": topic,
        "p_sentiment": sentiment,
        "p_source": source,
        "p_limit": limit,
    }).execute()

    return {
        "articles": [
            {
                "id": r["id"],
                "title": r["title"],
                "url": r["url"],
                "source_name": r["source_name"],
                "published_at": r["published_at"],
                "topic": r["topic"],
                "sentiment_label": r["sentiment_label"],
                "sentiment_score": round(float(r["sentiment_score"] or 0), 4),
                "is_flagged": r["is_flagged"],
            }
            for r in result.data
        ]
    }


@router.get("/flagged")
def get_flagged_articles(
    limit: int = Query(20, description="Max flagged articles to return"),
):
    sb = get_supabase()
    result = sb.rpc("rpc_flagged_articles", {"p_limit": limit}).execute()

    return {
        "articles": [
            {
                "id": r["id"],
                "title": r["title"],
                "url": r["url"],
                "source_name": r["source_name"],
                "suspicion_score": round(float(r["suspicion_score"] or 0), 4),
                "flag_reason": r["flag_reason"],
                "published_at": r["published_at"],
            }
            for r in result.data
        ]
    }
