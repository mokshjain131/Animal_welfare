"""GET /overview/metrics — dashboard stat cards."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter

from db.database import get_supabase

router = APIRouter()


@router.get("/metrics")
def get_metrics():
    sb = get_supabase()
    today = date.today()

    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    yesterday_start = today_start - timedelta(days=1)

    # Call the aggregate RPC
    result = sb.rpc("rpc_overview_metrics", {
        "p_today_start": today_start.isoformat(),
        "p_yesterday_start": yesterday_start.isoformat(),
    }).execute()

    row = result.data[0] if result.data else {}

    articles_today = int(row.get("articles_today") or 0)
    avg_sent = round(float(row.get("avg_sentiment_today") or 0), 4)
    avg_sent_yest = float(row.get("avg_sentiment_yesterday") or 0)
    avg_sent_vs = round(avg_sent - avg_sent_yest, 4) if row.get("avg_sentiment_yesterday") else 0.0
    active_topics = int(row.get("active_topics") or 0)
    misinfo_alerts = int(row.get("misinfo_alerts") or 0)

    # Determine label
    if avg_sent >= 0.6:
        label = "positive"
    elif avg_sent <= 0.4:
        label = "negative"
    else:
        label = "neutral"

    # Active spike
    spike_result = (
        sb.table("spike_events")
        .select("topic, multiplier, detected_at")
        .eq("is_active", True)
        .order("detected_at", desc=True)
        .limit(1)
        .execute()
    )

    spike_data = None
    if spike_result.data:
        s = spike_result.data[0]
        spike_data = {
            "topic": s["topic"],
            "multiplier": s["multiplier"],
            "detected_at": s["detected_at"],
        }

    return {
        "articles_today": articles_today,
        "avg_sentiment": avg_sent,
        "avg_sentiment_label": label,
        "avg_sentiment_vs_yesterday": avg_sent_vs,
        "active_topics": active_topics,
        "misinfo_alerts": misinfo_alerts,
        "active_spike": spike_data,
    }
