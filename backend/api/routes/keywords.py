"""GET /trending/keywords — top trending keyphrases."""

from fastapi import APIRouter

from db.database import get_supabase

router = APIRouter()


@router.get("/keywords")
def get_trending_keywords():
    sb = get_supabase()
    result = (
        sb.table("trending_keywords")
        .select("phrase, score, article_count, trend_direction, topic")
        .order("score", desc=True)
        .execute()
    )

    return {
        "keywords": [
            {
                "phrase": kw["phrase"],
                "score": kw["score"],
                "article_count": kw["article_count"],
                "trend_direction": kw["trend_direction"],
                "topic": kw["topic"],
            }
            for kw in result.data
        ]
    }
