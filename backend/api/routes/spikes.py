"""GET /spikes/active — currently active spike events."""

from fastapi import APIRouter

from db.database import get_supabase

router = APIRouter()


@router.get("/active")
def get_active_spikes():
    sb = get_supabase()
    result = (
        sb.table("spike_events")
        .select("topic, multiplier, article_count, weekly_avg, detected_at")
        .eq("is_active", True)
        .order("detected_at", desc=True)
        .execute()
    )

    return {
        "spikes": [
            {
                "topic": spike["topic"],
                "multiplier": spike["multiplier"],
                "article_count": spike["article_count"],
                "weekly_avg": spike["weekly_avg"],
                "detected_at": spike["detected_at"],
            }
            for spike in result.data
        ]
    }
