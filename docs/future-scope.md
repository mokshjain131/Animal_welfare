# Future Scope

This document outlines planned improvements and upgrade paths for the Animal Welfare News Sentiment Tracker. The v1 build deliberately chose simple, fast-to-deploy solutions. Each section below describes what the current limitation is, why it was acceptable for v1, and what the upgrade looks like.

---

## 1. Database — Supabase (PostgreSQL) → TimescaleDB

**Current:** Supabase hosts a standard PostgreSQL database. Daily summaries are pre-computed by the aggregator every 30 minutes and stored as flat rows.

**Limitation:** As the article volume grows into the hundreds of thousands (months of continuous ingestion), pre-computing summaries on every run becomes slow and the `daily_summaries` table grows unbounded.

**Upgrade:** Migrate to [TimescaleDB](https://www.timescale.com/) — a PostgreSQL extension that adds:
- **Hypertables** — automatic time-partitioned storage for `articles` and `daily_summaries`
- **Continuous aggregates** — materialised views that update incrementally rather than recomputing from scratch
- **Data retention policies** — auto-drop articles older than N months to cap storage costs

The schema is already designed for this: `published_at` and `date` columns are present on every time-series table. Migration would require exporting the existing Supabase data, moving to a TimescaleDB cloud instance, and updating the aggregator to use continuous aggregate views instead of manual INSERT/UPDATE logic.

---

## 2. NLP — HuggingFace Inference API → Fine-Tuned Domain Model

**Current:** Three NLP tasks (sentiment, topic classification, misinformation detection) run via the HuggingFace Inference API using general-purpose models:
- `facebook/bart-large-mnli` — zero-shot classification (handles both sentiment and topic)
- `mrm8488/bert-tiny-finetuned-fake-news-detection` — misinformation scoring

**Limitation:** These are general models not trained on animal welfare text. Zero-shot classification works well but has a ceiling — it cannot learn domain-specific signals (e.g. distinguishing "undercover investigation" from "routine inspection").

**Upgrade path:**
1. **Labelled dataset** — export the `articles` + `sentiment_scores` + `topics` tables, manually correct the labels for ~500 articles
2. **Fine-tune** a `distilbert-base-uncased` model on the corrected dataset using HuggingFace `Trainer`
3. **Host** on HuggingFace Hub as a private model endpoint
4. Swap the model IDs in `nlp/sentiment.py` and `nlp/topic_classifier.py` — the rest of the code stays identical

This would also allow replacing the current three candidate sentiment labels with a richer set mapped to specific movement outcomes.

---

## 3. Keyphrase Extraction — YAKE → KeyBERT (on a GPU endpoint)

**Current:** YAKE is used for keyphrase extraction — it's fast and requires no model, but it's purely statistical and context-blind.

**Limitation:** YAKE scores n-grams based on frequency and co-occurrence. It cannot distinguish "animal welfare violation" from "animal welfare success" — both score equally. It also generates noisy phrases from boilerplate (cookie notices, author bios) that slip past the text cleaner.

**Upgrade:** Switch back to `KeyBERT` backed by a domain-fine-tuned sentence-transformer, hosted on a dedicated HuggingFace GPU endpoint. Cost-effective once the fine-tuned model from point 2 exists — reuse the same embedding model.

---

## 4. Ingestion — APScheduler → Celery Beat

**Current:** APScheduler runs the pipeline as a background thread inside the FastAPI process. This means the pipeline and the API share memory and CPU.

**Limitation:** On Render's free tier, a compute-heavy pipeline run (scraping 200 URLs, 200 HuggingFace API calls) can starve the API of resources, causing request timeouts during pipeline execution. If the process crashes, the scheduler dies too.

**Upgrade:** Separate the pipeline into a Celery worker process backed by Redis as the broker:
- API server and worker run as separate Render services
- Pipeline failures don't affect API availability
- Can scale workers horizontally during high-volume runs
- Built-in retry logic and task result tracking

The pipeline logic in `scheduler.py` would move to a Celery task with minimal changes.

---

## 5. Relevance Filtering — Keyword List → ML Classifier

**Current:** `relevance_gate.py` filters articles by checking if any configured keyword appears in the title or text. Fast and transparent, but blunt.

**Limitation:** Misses articles that use synonyms or euphemistic industry language ("processing facilities" instead of "slaughterhouses"). Also passes through tangentially relevant articles that mention an animal species in a non-welfare context.

**Upgrade:** Train a binary classifier (`relevant` / `not relevant`) on a labelled sample of 1,000 fetched articles. A fine-tuned `distilbert` model for sequence classification would achieve high precision with minimal training data given the narrow domain. Deploy the same way as the fine-tuned sentiment model.

---

## 6. API → WebSocket Live Updates

**Current:** The frontend polls every 30 minutes using `setInterval` in each hook.

**Upgrade:** Add a FastAPI WebSocket endpoint that pushes a `pipeline_complete` event whenever `run_ingestion_pipeline()` finishes. The React dashboard listens and re-fetches only the panels that changed. Reduces unnecessary polling and makes the dashboard feel live.

---

## 7. Visualisation — Recharts → D3 Custom Charts

**Current:** All 9 panels use Recharts — good defaults, easy to configure, no custom rendering needed.

**When to upgrade:** Only if a specific visualisation requires behaviour Recharts can’t provide — for example:
- A **force-directed entity graph** showing which organisations and animal species appear together
- A **geographic heatmap** of welfare incident density by country
- A **narrative drift vector** chart showing sentiment direction over time per topic

D3 gives complete control over rendering but requires significantly more code. Do not upgrade just for aesthetics.

---

## 8. Caching — Add Redis if Response Times Degrade

**Current:** No caching layer. Every API request hits Supabase.

**Current performance:** All 10 endpoints respond under 300ms because they read from pre-computed summary tables, not raw articles.

**When to add Redis:** If the dashboard starts feeling sluggish after months of data accumulation (summary tables grow large) or if Render’s free-tier Supabase connection pool gets saturated, add Redis with a 5-minute TTL on all summary endpoints. The FastAPI route handlers are already isolated functions — wrapping them with `@cache` decorators would be a one-day change.

---

## Priority Order

| Priority | Upgrade | Impact | Effort |
|---|---|---|---|
| 1 | Fine-tuned NLP model | High — much better sentiment accuracy | Medium |
| 2 | ML relevance classifier | High — better signal-to-noise | Medium |
| 3 | Celery Beat | Medium — production stability | Medium |
| 4 | TimescaleDB | Medium — only needed at scale | High |
| 5 | Redis cache | Low — add only if needed | Low |
| 6 | WebSocket updates | Low — UX improvement | Low |
| 7 | D3 custom charts | Low — only for specific visuals | High |
