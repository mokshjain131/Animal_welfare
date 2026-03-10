"""Verify Module 6 — Scheduler & Main App.

Tests:
1. scheduler.py imports and functions exist
2. run_ingestion_pipeline() executes successfully
3. create_scheduler() returns a configured scheduler
4. main.py creates a FastAPI app with health endpoint
5. Full pipeline runs and populates the database
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

print("=" * 60)
print("MODULE 6 — Scheduler & Main App Verification")
print("=" * 60)

# ── 1. Import check ──────────────────────────────────────────────
print("\n--- 1. Import check ---")
from ingestion.scheduler import run_ingestion_pipeline, create_scheduler
print("  scheduler.py: run_ingestion_pipeline ✓")
print("  scheduler.py: create_scheduler ✓")

from main import create_app
print("  main.py: create_app ✓")

# ── 2. Create scheduler ─────────────────────────────────────────
print("\n--- 2. Scheduler creation ---")
scheduler = create_scheduler()
print(f"  Scheduler type: {type(scheduler).__name__}")
jobs = scheduler.get_jobs()
print(f"  Scheduled jobs: {len(jobs)}")
for job in jobs:
    print(f"    Job: {job.id} | trigger: {job.trigger}")
# Don't start it — we'll run the pipeline manually

# ── 3. Pre-pipeline DB state ────────────────────────────────────
print("\n--- 3. Pre-pipeline DB state ---")
from db.database import get_session_factory
from db.models import Article, SentimentScore, DailySummary, TrendingKeyword

db = get_session_factory()()

articles_before = db.query(Article).count()
processed_before = db.query(Article).filter(Article.is_processed == True).count()
print(f"  Articles: {articles_before} total, {processed_before} processed")

# ── 4. Run pipeline ─────────────────────────────────────────────
print("\n--- 4. Running pipeline (this fetches, scrapes, processes — may take a minute) ---")
run_ingestion_pipeline()

# ── 5. Post-pipeline DB state ───────────────────────────────────
print("\n--- 5. Post-pipeline DB state ---")
# Refresh session
db.expire_all()

articles_after = db.query(Article).count()
processed_after = db.query(Article).filter(Article.is_processed == True).count()
new_articles = articles_after - articles_before
new_processed = processed_after - processed_before

print(f"  Articles: {articles_after} total (+{new_articles} new)")
print(f"  Processed: {processed_after} total (+{new_processed} newly processed)")

summaries = db.query(DailySummary).count()
keywords = db.query(TrendingKeyword).count()
print(f"  Daily summaries: {summaries} rows")
print(f"  Trending keywords: {keywords} rows")

# ── 6. FastAPI app check ────────────────────────────────────────
print("\n--- 6. FastAPI app check ---")
from main import app
print(f"  App title: {app.title}")
print(f"  App version: {app.version}")

routes = [r.path for r in app.routes]
print(f"  Routes: {routes}")
if "/health" in routes:
    print("  Health endpoint: ✓")

# ── 7. Second pipeline (idempotency) ────────────────────────────
print("\n--- 7. Second pipeline run (idempotency check) ---")
run_ingestion_pipeline()

db.expire_all()
articles_final = db.query(Article).count()
# Should have same or more articles, but no crashes
print(f"  Articles after 2nd run: {articles_final} (was {articles_after})")
print(f"  Pipeline ran without errors ✓")

print("\n" + "=" * 60)
print("Module 6 verification complete!")
print("=" * 60)

db.close()
