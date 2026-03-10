# System Architecture

## Overview

The system is organised into six layers. Data flows top to bottom — from external sources through ingestion, NLP enrichment, storage, and API to the React dashboard.

---

## Layer 1 — Data Sources

| Source | Description | Output |
|---|---|---|
| **RSS Feeds** | Free, no API key. BBC, Reuters, AP, advocacy outlets. | Title, URL, timestamp, description |
| **NewsAPI** | Keyword search across 80,000+ sources. 100 requests/day on free tier. | Headlines and URLs |
| **Trafilatura** | Scraper layer. Extracts full article body from URLs. Falls back to title + description if under 150 characters. | Full article text |

> **Data passed down:** raw article objects — `title`, `url`, `text`, `source_name`, `published_at`, `source_type`

---

## Layer 2 — Ingestion

| Component | Responsibility |
|---|---|
| **Scheduler** (APScheduler) | Triggers full ingestion run every 15–30 minutes. Starts automatically with FastAPI on app launch. |
| **Normalizer** | Merges all sources into one standard article schema. Downstream layers never see source differences. |
| **Deduplicator** | URL lookup against `articles` table. One URL = one article. Skips if already seen. |
| **Relevance Gate** | Keyword filter discards articles with no animal welfare signal. Runs before any expensive NLP model is invoked. |

> **Data passed down:** cleaned, deduplicated, relevant articles only

---

## Layer 3 — NLP Engine

### spaCy
- Named Entity Recognition (orgs, locations, animal species)
- Keyword and keyphrase extraction
- Sentence segmentation
- Text cleaning and tokenization

### HuggingFace
- Sentiment analysis: `pos` / `neg` / `neutral` + confidence score
- Topic classification: assigns category to each article
- Misinformation suspicion scoring
- Narrative framing signal detection

### KeyBERT
- Semantic keyphrase extraction per article
- Top 3–5 phrases stored alongside article in database
- Feeds the Trending Keywords panel

### TF-IDF *(runs in Summary Aggregator, not per article)*
- Corpus-level term frequency analysis
- Detects statistically spiking terms vs 7-day baseline
- Runs every 30 minutes on last 24 hours of articles

> **Data passed down:** enriched articles — `sentiment_score`, `topic`, `entities`, `keyphrases`, `misinfo_flag`

---

## Layer 4 — Storage

### PostgreSQL *(primary store, TimescaleDB-ready schema)*

| Table | Purpose |
|---|---|
| `articles` | Raw and normalised article records |
| `sentiment_scores` | Per-article HuggingFace sentiment output |
| `daily_summaries` | Pre-computed daily rollups per topic |
| `topics` | Topic classifications per article |
| `flagged_articles` | Articles exceeding misinformation threshold |
| `trending_keywords` | Top trending keyphrases, overwritten every 30 min |
| `spike_events` | Detected narrative spike records |
| `entities` | Named entities extracted per article |

### Summary Aggregator *(scheduled every 30 minutes)*
- Writes pre-computed rows to `daily_summaries`
- Updates `trending_keywords` and `spike_events`
- Mirrors TimescaleDB continuous aggregates manually

> **Redis** — deferred, add later if dashboard feels slow.

> **Data passed down:** JSON via REST API (FastAPI)

---

## Layer 5 — API Layer

**FastAPI (Python)** — REST API serving pre-computed data from PostgreSQL. Auto-generates interactive documentation at `/docs`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/overview/metrics` | Dashboard stat cards |
| `GET` | `/sentiment/trend` | Daily sentiment over time |
| `GET` | `/topics/volume` | Article counts per topic |
| `GET` | `/narrative/shifts` | Topic volume over time |
| `GET` | `/articles/flagged` | Misinformation review queue |
| `GET` | `/articles/recent` | Latest articles feed |
| `GET` | `/trending/keywords` | Top trending keyphrases |
| `GET` | `/entities/top` | Top orgs, locations, species |
| `GET` | `/spikes/active` | Active spike events |
| `GET` | `/sources/sentiment` | Per-source sentiment breakdown |

> **Data passed down:** HTTP responses to React frontend

---

## Layer 6 — Dashboard

- **React + Recharts** — 9 active panels
- **D3** — deferred, only if Recharts cannot handle a specific visualisation

### Design Intent

The layout tells a story **top to bottom**:

```
situation awareness → trend context → narrative intelligence → live feed → language intelligence
```

A strategist should be able to answer four questions **in under 60 seconds**:

1. **What is happening right now?** → Overview Metrics Bar + Story Spike Banner
2. **Is coverage improving or worsening?** → Sentiment Trend + Narrative Shift charts
3. **Are there any threats to respond to?** → Misinformation Alerts Panel
4. **What specific stories should I read?** → Latest Articles Feed

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  ROW 1 — Situation Awareness                                        │
│  Overview Metrics Bar — full width                                  │
│  Articles Today · Avg Sentiment · Active Topics · Misinfo · Spikes  │
├────────────────────────────────────┬────────────────────────────────┤
│  ROW 2 — Trend Context             │                                │
│  Sentiment Trend Over Time (2/3)   │  Topic Distribution (1/3)     │
│  Line chart, topic filter, range   │  Bar chart, counts per topic  │
├────────────────────────────────────┼────────────────────────────────┤
│  ROW 3 — Narrative Intelligence    │                                │
│  Narrative Shift Detector (2/3)    │  Misinformation Alerts (1/3)  │
│  Stacked area, topic volume        │  Review queue, scores         │
├──────────────────────────────────────────────────┬─────────────────┤
│  ROW 4 — Live Feed                               │                 │
│  Latest Articles Feed (3/4)                      │  Source         │
│  Scrollable, filterable                          │  Sentiment (1/4)│
│  headline · source · topic · sentiment           │  Per-source bars│
├──────────────────────────────────────┬──────────────────────────────┤
│  ROW 5 — Entity & Language Intel     │                              │
│  Top Entities Mentioned (1/2)        │  Trending Keywords (1/2)    │
│  Orgs · Locations · Species          │  Top 10 phrases · trends    │
└──────────────────────────────────────┴──────────────────────────────┘
```
