"""Migrate data from local PostgreSQL to Supabase.

Usage:
    cd backend
    uv run python scripts/migrate_to_supabase.py

Prerequisites:
    1. Tables must already exist in Supabase (run init.sql + supabase_rpc_functions.sql
       in the Supabase SQL Editor first).
    2. Set SUPABASE_URL and SUPABASE_KEY in backend/.env
    3. Local Postgres must be running with data.
"""

import sys
from pathlib import Path

# Ensure backend/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from supabase import create_client

# ── Config ───────────────────────────────────────────────────────────
LOCAL_DB_URL = "postgresql://postgres:password@localhost:5432/sentiment_tracker"

# Load Supabase creds from settings
from config.settings import settings
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY

# Tables in dependency order (parents first)
TABLES = [
    "articles",
    "sentiment_scores",
    "topics",
    "entities",
    "flagged_articles",
    "keyphrases",
    "trending_keywords",
    "daily_summaries",
    "spike_events",
]


def migrate():
    print("Connecting to local PostgreSQL...")
    engine = create_engine(LOCAL_DB_URL)

    print(f"Connecting to Supabase: {SUPABASE_URL}")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    with engine.connect() as conn:
        for table in TABLES:
            print(f"\n── Migrating: {table} ──")

            # Read all rows as dicts
            result = conn.execute(text(f"SELECT * FROM {table} ORDER BY id"))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

            if not rows:
                print(f"  (empty — 0 rows)")
                continue

            print(f"  Found {len(rows)} rows")

            # Serialize datetime/date objects to ISO strings
            for row in rows:
                for key, val in row.items():
                    if hasattr(val, "isoformat"):
                        row[key] = val.isoformat()

            # Insert in batches of 500 (Supabase limit)
            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]
                try:
                    sb.table(table).upsert(batch).execute()
                    print(f"  Inserted batch {i // batch_size + 1} ({len(batch)} rows)")
                except Exception as e:
                    print(f"  ERROR inserting batch: {e}")
                    # Try row by row for this batch
                    for j, row in enumerate(batch):
                        try:
                            sb.table(table).upsert(row).execute()
                        except Exception as e2:
                            print(f"    Row {i + j} failed: {e2}")

    print("\n✅ Migration complete!")
    print("You can now stop local PostgreSQL and run the app with Supabase.")


if __name__ == "__main__":
    migrate()
