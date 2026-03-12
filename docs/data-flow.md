# Data Flow — End to End

This document traces a single pipeline run from scheduler trigger to rendered dashboard panel.

---

## Step 1 — Scheduler Trigger

**APScheduler** triggers every 15–30 minutes.  
Starts inside FastAPI on app startup. Fires the ingestion pipeline on schedule automatically.

---

## Step 2 — Article Fetch

**RSS Feeds + NewsAPI** fetch article URLs and metadata.

- RSS parsed as XML
- NewsAPI called with animal welfare keyword queries
- Both return: `title`, `url`, `source_name`, `timestamp`

---

## Step 3 — Full Text Extraction

**Trafilatura** scrapes full article text from URLs.

- If returned text is under ~150 characters, falls back to `title + description`
- Failure is logged but pipeline continues without interruption

---

## Step 4 — Normalisation

**Normalizer** produces standard article objects.

All sources merged into a single schema:

```json
{
  "title": "...",
  "full_text": "...",
  "source_name": "...",
  "url": "...",
  "published_at": "...",
  "source_type": "rss | newsapi"
}
```

Nothing downstream sees source differences.

---

## Step 5 — Deduplication

**Deduplicator** checks URL against Supabase — skips if already seen.  
Prevents duplicate NLP runs and inflated metrics.

---

## Step 6 — Relevance Gate

**Relevance Gate** filters non-animal-welfare articles.

- Keyword check against configurable topic list
- Articles with no match are logged and discarded
- Runs **before** any NLP model is invoked

---

## Step 7 — spaCy Preprocessing

**spaCy** preprocesses text:

- NER extracts organisations, locations, and animal species
- Text is cleaned, tokenized, and segmented for downstream transformer models

---

## Step 8 — HuggingFace Classification

**HuggingFace** classifies each article:

| Output | Description |
|---|---|
| Sentiment | `pos` / `neg` / `neutral` + confidence score |
| Topic | Category assigned per article |
| Misinformation | Suspicion score returned |
| Narrative framing | Signal detected |

---

## Step 9 — Keyphrase Extraction

**KeyBERT** extracts top keyphrases per article:

- Returns top 3–5 semantic keyphrases
- Stored alongside the article record in the database

---

## Step 10 — Database Write

Enriched article saved to **Supabase** (cloud-hosted PostgreSQL).

`article`, `sentiment_score`, `topic`, `entities`, `keyphrases`, and `misinfo_flag` all written to their respective tables via the Supabase SDK.

---

## Step 11 — Summary Aggregation

**Summary Aggregator** runs every 30 minutes:

- Writes pre-computed rows to `daily_summaries`
- Runs TF-IDF across last 24 hours of articles vs 7-day baseline
- Computes spike detection logic
- Updates `trending_keywords` and `spike_events` tables

---

## Step 12 — API Serving

**FastAPI** serves pre-computed data to the React dashboard via 10 REST endpoints. Each endpoint calls Supabase RPC functions or table queries through the `supabase-py` SDK.

> The dashboard **never runs raw aggregation queries** — it always reads from pre-computed summary tables for fast response times.

---

## Step 13 — Dashboard Rendering

**React** renders 9 active panels:

| Panel | Source |
|---|---|
| Overview Metrics Bar | `/overview/metrics` |
| Sentiment Trend Over Time | `/sentiment/trend` |
| Narrative Shift Detector | `/narrative/shifts` |
| Story Spike Detector (banner) | `/spikes/active` |
| Misinformation Alerts Panel | `/articles/flagged` |
| Trending Keywords | `/trending/keywords` |
| Top Entities Mentioned | `/entities/top` |
| Topic Distribution | `/topics/volume` |
| Latest Articles Feed | `/articles/recent` |
| Source Sentiment Comparison | `/sources/sentiment` |

> **D3 Custom Visualisations** — deferred.
