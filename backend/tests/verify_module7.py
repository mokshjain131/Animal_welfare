"""Verify Module 7 — REST API endpoints.

Starts the FastAPI app via TestClient (no uvicorn needed) and tests all 10 endpoints.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(level=logging.WARNING)

# Prevent the lifespan from running the full pipeline during tests
os.environ["SKIP_PIPELINE"] = "1"

from fastapi.testclient import TestClient

print("=" * 60)
print("MODULE 7 — REST API Verification")
print("=" * 60)

# We need to import the app but skip the lifespan pipeline run.
# Patch the lifespan to skip pipeline for testing.
from main import app

client = TestClient(app, raise_server_exceptions=False)

results = []


def test_endpoint(method, path, expected_keys=None, params=None):
    """Test a single endpoint and report results."""
    url = path
    resp = client.get(url, params=params)
    status = resp.status_code
    ok = status == 200

    if ok and expected_keys:
        data = resp.json()
        for key in expected_keys:
            if key not in data:
                ok = False
                break

    label = "OK" if ok else "FAIL"
    detail = ""
    if ok:
        data = resp.json()
        # Show a compact summary of the response
        if isinstance(data, dict):
            sizes = {}
            for k, v in data.items():
                if isinstance(v, list):
                    sizes[k] = f"{len(v)} items"
                elif v is None:
                    sizes[k] = "null"
                else:
                    sizes[k] = str(v)[:50]
            detail = str(sizes)
        else:
            detail = str(data)[:100]
    else:
        detail = f"status={status} body={resp.text[:200]}"

    results.append((label, path, params or {}, detail))
    print(f"  {label}  {path} {params or ''}")
    if not ok:
        print(f"        {detail}")
    return ok, resp.json() if ok else None


# ── 1. Health ────────────────────────────────────────────────────
print("\n--- 1. Health ---")
test_endpoint("GET", "/health", ["status"])

# ── 2. Overview Metrics ──────────────────────────────────────────
print("\n--- 2. Overview Metrics ---")
test_endpoint("GET", "/overview/metrics", [
    "articles_today", "avg_sentiment", "avg_sentiment_label",
    "avg_sentiment_vs_yesterday", "active_topics", "misinfo_alerts", "active_spike",
])

# ── 3. Sentiment Trend ──────────────────────────────────────────
print("\n--- 3. Sentiment Trend ---")
test_endpoint("GET", "/sentiment/trend", ["data"])
test_endpoint("GET", "/sentiment/trend", ["data"], params={"topic": "wildlife", "days": 30})

# ── 4. Topics Volume ────────────────────────────────────────────
print("\n--- 4. Topics Volume ---")
test_endpoint("GET", "/topics/volume", ["data"])
test_endpoint("GET", "/topics/volume", ["data"], params={"days": 30})

# ── 5. Narrative Shifts ─────────────────────────────────────────
print("\n--- 5. Narrative Shifts ---")
test_endpoint("GET", "/narrative/shifts", ["dates", "series"])
test_endpoint("GET", "/narrative/shifts", ["dates", "series"], params={"days": 7})

# ── 6. Articles Recent ──────────────────────────────────────────
print("\n--- 6. Articles Recent ---")
ok, data = test_endpoint("GET", "/articles/recent", ["articles"])
if ok and data:
    print(f"        → {len(data['articles'])} articles returned")

test_endpoint("GET", "/articles/recent", ["articles"], params={"sentiment": "positive", "limit": 5})
test_endpoint("GET", "/articles/recent", ["articles"], params={"topic": "wildlife"})

# ── 7. Articles Flagged ─────────────────────────────────────────
print("\n--- 7. Articles Flagged ---")
ok, data = test_endpoint("GET", "/articles/flagged", ["articles"])
if ok and data:
    print(f"        → {len(data['articles'])} flagged articles")

# ── 8. Trending Keywords ────────────────────────────────────────
print("\n--- 8. Trending Keywords ---")
ok, data = test_endpoint("GET", "/trending/keywords", ["keywords"])
if ok and data:
    print(f"        → {len(data['keywords'])} keywords")

# ── 9. Entities Top ─────────────────────────────────────────────
print("\n--- 9. Entities Top ---")
ok, data = test_endpoint("GET", "/entities/top", ["organizations", "locations", "animals"])
if ok and data:
    print(f"        → orgs={len(data['organizations'])}, locs={len(data['locations'])}, animals={len(data['animals'])}")

test_endpoint("GET", "/entities/top", ["organizations", "locations", "animals"], params={"days": 30, "limit": 3})

# ── 10. Spikes Active ───────────────────────────────────────────
print("\n--- 10. Spikes Active ---")
ok, data = test_endpoint("GET", "/spikes/active", ["spikes"])
if ok and data:
    print(f"        → {len(data['spikes'])} active spikes")

# ── 11. Sources Sentiment ───────────────────────────────────────
print("\n--- 11. Sources Sentiment ---")
ok, data = test_endpoint("GET", "/sources/sentiment", ["sources"])
if ok and data:
    print(f"        → {len(data['sources'])} sources")

test_endpoint("GET", "/sources/sentiment", ["sources"], params={"days": 30, "limit": 5})

# ── Summary ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == "OK")
failed = sum(1 for r in results if r[0] == "FAIL")
print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")

if failed:
    print("\nFailed tests:")
    for r in results:
        if r[0] == "FAIL":
            print(f"  {r[1]} {r[2]} — {r[3]}")

print("=" * 60)
