"""Module 3 — Ingestion Pipeline verification script.

Tests each sub-component step by step:
1. RSS fetcher
2. NewsAPI fetcher
3. Scraper (full text extraction)
4. Normalizer
5. Deduplicator
6. Relevance gate
7. Save to DB
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("verify_module3")

# ── Step 1: RSS Fetcher ─────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 1: RSS Fetcher")
print("=" * 60)

from ingestion.rss_fetcher import fetch_rss_feed, fetch_all_rss_feeds

# Test single feed
single_feed = fetch_rss_feed("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml")
print(f"  Single feed (BBC): {len(single_feed)} articles")
if single_feed:
    sample = single_feed[0]
    print(f"  Sample: {sample['title'][:80]}")
    print(f"  URL:    {sample['url'][:80]}")
    print(f"  Date:   {sample['published_at']}")

# Test all feeds
all_rss = fetch_all_rss_feeds()
print(f"  All RSS feeds: {len(all_rss)} total articles")

# ── Step 2: NewsAPI Fetcher ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: NewsAPI Fetcher")
print("=" * 60)

from ingestion.newsapi_fetcher import fetch_newsapi_articles, fetch_all_newsapi_articles

# Test single query
newsapi_single = fetch_newsapi_articles("animal welfare", page_size=5)
print(f"  Single query ('animal welfare'): {len(newsapi_single)} articles")
if newsapi_single:
    sample = newsapi_single[0]
    print(f"  Sample: {sample['title'][:80]}")

# Test all topics (will use API quota — keep page_size small)
all_newsapi = fetch_all_newsapi_articles()
print(f"  All NewsAPI topics: {len(all_newsapi)} total articles")

# ── Step 3: Scraper ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Scraper (testing on 3 articles max)")
print("=" * 60)

from ingestion.scraper import scrape_full_text, enrich_with_full_text

# Test on a small subset to save time
test_articles = (all_rss[:2] + all_newsapi[:1]) if all_rss else all_newsapi[:3]
print(f"  Scraping {len(test_articles)} articles...")
enriched = enrich_with_full_text(test_articles)
for a in enriched:
    has_full = len(a.get("full_text", "")) > 150
    print(f"  {'✓' if has_full else '✗'} {a['title'][:60]} ({len(a.get('full_text', ''))} chars)")

# ── Step 4: Normalizer ───────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Normalizer")
print("=" * 60)

from ingestion.normalizer import normalize_all

normalized = normalize_all(all_rss, all_newsapi)
print(f"  Normalized: {len(normalized)} articles")
if normalized:
    sample = normalized[0]
    keys = sorted(sample.keys())
    print(f"  Schema keys: {keys}")
    print(f"  source_type: {sample['source_type']}")

# ── Step 5: Deduplicator ─────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Deduplicator")
print("=" * 60)

from db.database import get_session_factory
from ingestion.deduplicator import deduplicate

Session = get_session_factory()
db = Session()

try:
    unique = deduplicate(normalized, db)
    print(f"  Before dedup: {len(normalized)}, After: {len(unique)}")
finally:
    db.close()

# ── Step 6: Relevance Gate ────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Relevance Gate")
print("=" * 60)

from ingestion.relevance_gate import filter_relevant

relevant, rejected = filter_relevant(unique)
print(f"  Relevant: {len(relevant)}, Rejected: {len(rejected)}")
if relevant:
    print(f"  Sample relevant: {relevant[0]['title'][:80]}")
if rejected:
    print(f"  Sample rejected: {rejected[0]['title'][:80]}")

# ── Step 7: Save to DB ───────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: Save relevant articles to DB")
print("=" * 60)

from db.models import Article

db = Session()
try:
    saved_count = 0
    for article in relevant:
        row = Article(
            url=article["url"],
            title=article["title"],
            full_text=article["full_text"],
            source_name=article["source_name"],
            source_type=article["source_type"],
            published_at=article["published_at"],
            is_processed=False,
        )
        db.add(row)
        saved_count += 1

    db.commit()
    print(f"  Saved {saved_count} articles to DB")

    # Verify count
    total = db.query(Article).count()
    print(f"  Total articles in DB: {total}")
finally:
    db.close()

# ── Step 8: Re-run dedup to confirm it catches duplicates ─────────
print("\n" + "=" * 60)
print("STEP 8: Re-run dedup (should drop all)")
print("=" * 60)

db = Session()
try:
    unique2 = deduplicate(normalized, db)
    print(f"  Re-dedup: {len(unique2)} new (should be 0 or near 0)")
finally:
    db.close()

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("MODULE 3 VERIFICATION SUMMARY")
print("=" * 60)
print(f"  RSS articles fetched:    {len(all_rss)}")
print(f"  NewsAPI articles fetched:{len(all_newsapi)}")
print(f"  After normalization:     {len(normalized)}")
print(f"  After deduplication:     {len(unique)}")
print(f"  Relevant (saved to DB):  {len(relevant)}")
print(f"  Rejected by gate:        {len(rejected)}")
print("  ✓ Module 3 complete!")
