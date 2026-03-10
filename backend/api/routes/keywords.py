"""GET /trending/keywords — top trending keyphrases."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import TrendingKeyword

router = APIRouter()


@router.get("/keywords")
def get_trending_keywords(db: Session = Depends(get_db)):
    rows = (
        db.query(TrendingKeyword)
        .order_by(TrendingKeyword.score.desc())
        .all()
    )

    return {
        "keywords": [
            {
                "phrase": kw.phrase,
                "score": kw.score,
                "article_count": kw.article_count,
                "trend_direction": kw.trend_direction,
                "topic": kw.topic,
            }
            for kw in rows
        ]
    }
