"""GET /spikes/active — currently active spike events."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import SpikeEvent

router = APIRouter()


@router.get("/active")
def get_active_spikes(db: Session = Depends(get_db)):
    rows = (
        db.query(SpikeEvent)
        .filter(SpikeEvent.is_active == True)
        .order_by(SpikeEvent.detected_at.desc())
        .all()
    )

    return {
        "spikes": [
            {
                "topic": spike.topic,
                "multiplier": spike.multiplier,
                "article_count": spike.article_count,
                "weekly_avg": spike.weekly_avg,
                "detected_at": spike.detected_at.isoformat() if spike.detected_at else None,
            }
            for spike in rows
        ]
    }
