"""Verify Module 5 — Aggregator."""

import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

from db.database import get_session_factory
from db.models import Article, DailySummary, TrendingKeyword, SpikeEvent

db = get_session_factory()()

print("=" * 60)
print("MODULE 5 — Aggregator Verification")
print("=" * 60)

# ── Pre-check: how many processed articles do we have? ───────────
total_articles = db.query(Article).count()
processed = db.query(Article).filter(Article.is_processed == True).count()
print(f"\nArticles in DB: {total_articles} total, {processed} processed")

# ── 1. Daily summaries ───────────────────────────────────────────
print("\n--- 1. Daily summaries ---")
from aggregator.daily_summary import compute_daily_summaries, compute_historical_summaries

# Run historical to backfill
compute_historical_summaries(db, days_back=7)
# Run today's
compute_daily_summaries(db)

summary_count = db.query(DailySummary).count()
print(f"Rows in daily_summaries: {summary_count}")

# Show sample rows
summaries = db.query(DailySummary).order_by(DailySummary.date.desc()).limit(10).all()
for s in summaries:
    print(f"  {s.date} | {s.topic:20s} | articles={s.article_count} | "
          f"avg_sent={s.avg_sentiment:.4f} | +{s.positive_count} -{s.negative_count} ~{s.neutral_count}")

# ── 2. Trending keywords ─────────────────────────────────────────
print("\n--- 2. Trending keywords ---")
from aggregator.tfidf_keywords import compute_trending_keywords

compute_trending_keywords(db)

kw_count = db.query(TrendingKeyword).count()
print(f"Rows in trending_keywords: {kw_count}")

keywords = db.query(TrendingKeyword).order_by(TrendingKeyword.score.desc()).all()
for kw in keywords:
    print(f"  {kw.phrase:40s} | score={kw.score:.4f} | count={kw.article_count} | trend={kw.trend_direction}")

# ── 3. Spike detection ───────────────────────────────────────────
print("\n--- 3. Spike detection ---")
from aggregator.spike_detector import detect_spikes, compute_weekly_average

# Show weekly averages for each topic
from config.keywords import get_topic_labels
for topic in get_topic_labels():
    avg = compute_weekly_average(topic, db)
    print(f"  Weekly avg for {topic:20s}: {avg:.2f}")

new_spikes = detect_spikes(db)
spike_count = db.query(SpikeEvent).count()
active_spikes = db.query(SpikeEvent).filter(SpikeEvent.is_active == True).count()
print(f"\nSpike events total: {spike_count} (active: {active_spikes})")
if new_spikes:
    for sp in new_spikes:
        print(f"  NEW SPIKE: {sp['topic']} — {sp['today_count']} articles ({sp['multiplier']:.1f}× avg)")
else:
    print("  No new spikes (expected if article volume is low)")

# ── 4. Idempotency check ─────────────────────────────────────────
print("\n--- 4. Idempotency check ---")
from aggregator.spike_detector import run_aggregator

# Run aggregator twice
run_aggregator(db)
count_after_first = db.query(DailySummary).count()

run_aggregator(db)
count_after_second = db.query(DailySummary).count()

if count_after_first == count_after_second:
    print(f"  PASS — daily_summaries count unchanged: {count_after_first}")
else:
    print(f"  FAIL — count changed from {count_after_first} to {count_after_second}")

kw_after_first = db.query(TrendingKeyword).count()
print(f"  trending_keywords count: {kw_after_first} (should be stable)")

print("\n" + "=" * 60)
print("Module 5 verification complete!")
print("=" * 60)

db.close()
