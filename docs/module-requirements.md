# Module Requirements

Each module is self-contained, independently buildable, and has a single clear responsibility. Build them in order — each depends on the previous one working correctly.

---

## Module 1 — Database & Schema

**Responsibility:** Define and initialize the entire database schema. Everything else depends on this — build it first.

### What it does
- Defines all database tables (PostgreSQL hosted on Supabase)
- Provides a Supabase client singleton for all modules to use
- Schema managed via SQL files run in the Supabase SQL Editor
- Server-side RPC functions for complex aggregate queries

### Tables

| Table | Description |
|---|---|
| `articles` | Raw article records |
| `sentiment_scores` | Per-article sentiment output |
| `topics` | Topic classifications |
| `entities` | Named entities extracted per article |
| `flagged_articles` | Articles exceeding misinfo threshold |
| `trending_keywords` | Pre-computed trending phrases |
| `daily_summaries` | Pre-computed daily rollups |
| `spike_events` | Detected narrative spikes |

### Files

```
backend/db/
    database.py          # Supabase client singleton (get_supabase())
    models.py            # SQLAlchemy table definitions (schema reference)
    migrations/
        init.sql         # raw SQL to create all tables (run in Supabase SQL Editor)
        supabase_rpc_functions.sql  # server-side RPC functions
        fix_sequences.sql           # reset auto-increment after migration
backend/scripts/
    migrate_to_supabase.py  # one-time data migration from local PostgreSQL
```

**Done when:** You can connect to Supabase, run `init.sql` + `supabase_rpc_functions.sql`, and see all tables created correctly.  
**Depends on:** Nothing. This is the foundation.

---

## Module 2 — Configuration & Settings

**Responsibility:** Centralise all configuration — API keys, environment variables, keyword lists, topic definitions, thresholds.

### What it does
- Loads all environment variables from `.env`
- Defines `SUPABASE_URL` and `SUPABASE_KEY` for database connection
- Defines the animal welfare keyword list per topic
- Defines topic categories
- Defines thresholds (spike multiplier `2Ã—`, misinfo confidence cutoff, fallback text length `150` chars)

### Files

```
backend/config/
    settings.py          # loads env vars, API keys, all config values
    keywords.py          # keyword lists per topic category
```

### Keyword Structure

```python
TOPIC_KEYWORDS = {
    "factory_farming":   ["factory farm", "industrial farming", "battery cage", ...],
    "animal_testing":    ["animal testing", "vivisection", "lab animals", ...],
    "wildlife":          ["wildlife", "poaching", "habitat destruction", ...],
    "pet_welfare":       ["animal cruelty", "pet abuse", "dog fighting", ...],
    "animal_policy":     ["animal welfare law", "animal rights bill", ...],
    "veganism":          ["vegan", "plant-based", "meat industry", ...]
}
```

**Done when:** You can import `settings` anywhere and get correct values. Keywords are organised and easy to extend.  
**Depends on:** Nothing.

---

## Module 3 — Ingestion Pipeline

**Responsibility:** Fetch articles from all three sources, extract full text, normalize into one schema, deduplicate, and filter for relevance.

### Sub-components

| Component | Responsibility |
|---|---|
| **RSS Fetcher** | Parses XML from configured feed URLs |
| **NewsAPI Fetcher** | Calls NewsAPI with animal welfare keyword queries |
| **Trafilatura Scraper** | Extracts full text or falls back to `title + description` |
| **Normalizer** | Merges all sources into one standard article schema |
| **Deduplicator** | Checks URL against `articles` table, drops already-seen articles |
| **Relevance Gate** | Drops articles with no animal welfare signal, logs rejected articles |

### Files

```
backend/ingestion/
    rss_fetcher.py
    newsapi_fetcher.py
    scraper.py
    normalizer.py
    deduplicator.py
    relevance_gate.py
```

**Done when:** You can run the ingestion pipeline manually and see new relevant articles appearing in the `articles` table. No NLP yet — just raw articles saved.  
**Depends on:** Module 1 (database), Module 2 (config, keywords)

---

## Module 4 — NLP Pipeline

**Responsibility:** Take a cleaned article and enrich it with all NLP outputs. This module never fetches articles — it only processes what ingestion provides.

### Sub-components

| Component | Tool | Output |
|---|---|---|
| **spaCy Processor** | spaCy `en_core_web_sm` | NER (orgs, locations, species), cleaned + tokenized text |
| **Sentiment Analyser** | HuggingFace | `pos`/`neg`/`neutral` label + confidence score |
| **Topic Classifier** | HuggingFace zero-shot | Topic category + confidence score |
| **Misinformation Detector** | HuggingFace | Suspicion score 0â€“1, flag if above threshold |
| **KeyBERT Extractor** | KeyBERT | Top 3â€“5 semantic keyphrases with relevance scores |
| **NLP Pipeline Orchestrator** | `pipeline.py` | Calls all of the above in sequence, returns enriched article |

### Files

```
backend/nlp/
    pipeline.py              # orchestrator, calls everything in order
    spacy_processor.py
    sentiment.py
    topic_classifier.py
    misinfo_detector.py
    keybert_extractor.py
```

**Done when:** You can pass a single article object into `pipeline.py` and get back a fully enriched article with sentiment score, topic, entities, keyphrases, and misinfo flag.  
**Depends on:** Module 2 (config, thresholds)

---

## Module 5 — Aggregator

**Responsibility:** Run scheduled computations on the full article corpus to produce pre-computed summary data. This is what makes the dashboard fast.

### Sub-components

| Component | Schedule | Description |
|---|---|---|
| **Daily Summary Writer** | Every 30 min | Computes avg sentiment per topic per day, writes to `daily_summaries` |
| **TF-IDF Keyword Computer** | Every 30 min | Runs TF-IDF on last 24 hours vs 7-day baseline, writes to `trending_keywords` |
| **Spike Detector** | Every 30 min | Computes today vs rolling average per topic, writes `spike_events` |

### Files

```
backend/aggregator/
    daily_summary.py
    tfidf_keywords.py
    spike_detector.py
```

**Done when:** After running the aggregator manually, you can query `daily_summaries`, `trending_keywords`, and `spike_events` and see populated, accurate data.  
**Depends on:** Module 1 (database), Module 2 (config)

---

## Module 6 — Scheduler

**Responsibility:** Tie ingestion, NLP, and aggregation together into one automated pipeline that runs on a schedule.

### What it does
- Defines the full pipeline job: fetch â†’ normalize â†’ deduplicate â†’ filter â†’ NLP â†’ save â†’ aggregate
- Registers the job with APScheduler to run every 15â€“30 minutes
- Starts the scheduler when FastAPI launches
- Logs each run with start time, articles processed, and errors

### Pipeline Execution Order

```
1. RSS Fetcher         â†’ raw articles
2. NewsAPI Fetcher     â†’ raw articles
3. Scraper             â†’ adds full text to each
4. Normalizer          â†’ standard schema
5. Deduplicator        â†’ removes already-seen
6. Relevance Gate      â†’ removes irrelevant
7. NLP Pipeline        â†’ enriches each article
8. Save to Supabase    â†' writes all tables via Supabase SDK
9. Aggregator          â†’ updates summary tables
```

### Files

```
backend/
    main.py                      # FastAPI app + scheduler startup
    ingestion/
        scheduler.py             # job definitions, pipeline orchestration
```

**Done when:** Start the FastAPI app, wait 30 minutes, and the entire pipeline runs automatically. Articles in the database, enriched with NLP, summary tables populated.  
**Depends on:** All previous modules (1â€“5)

---

## Module 7 — REST API

**Responsibility:** Expose pre-computed data from Supabase to the frontend via clean REST endpoints. Uses the Supabase Python SDK and server-side RPC functions. This module never computes anything — it only reads from summary tables.

### Endpoints

| File | Method | Path | Returns |
|---|---|---|---|
| `metrics.py` | `GET` | `/overview/metrics` | Article count today, avg sentiment, active topic count, misinfo alert count, active spike |
| `sentiment.py` | `GET` | `/sentiment/trend` | Daily avg sentiment per topic over time |
| `topics.py` | `GET` | `/topics/volume` | Article count per topic for date range |
| `narrative.py` | `GET` | `/narrative/shifts` | Topic mention volume over time (for area chart) |
| `articles.py` | `GET` | `/articles/recent` | Latest N articles with all NLP fields |
| `articles.py` | `GET` | `/articles/flagged` | Articles above misinfo threshold |
| `keywords.py` | `GET` | `/trending/keywords` | Top 10 trending phrases with trend direction |
| `entities.py` | `GET` | `/entities/top` | Top orgs, locations, species |
| `spikes.py` | `GET` | `/spikes/active` | Currently active spike events |
| `sources.py` | `GET` | `/sources/sentiment` | Avg sentiment per source, top 10 by volume |

**Done when:** Every endpoint returns real data when called. Test all endpoints via FastAPI's auto-generated docs at `/docs` before touching the frontend.  
**Depends on:** Module 1 (database), Module 2 (config)

---

## Module 8 — Frontend Dashboard

**Responsibility:** Consume the API and render the dashboard. Each panel is an independent component that owns its own data-fetching hook.

### Shared Utilities *(build first)*

```
frontend/src/
    utils/api.js           # base API client
    utils/constants.js     # topic names, color maps, thresholds
    utils/formatters.js    # date formatting, score display

    shared/
        SentimentBadge.jsx
        TopicBadge.jsx
        SpikeBanner.jsx
        MisinfoFlag.jsx
        LoadingSpinner.jsx
```

### Panels *(build in dashboard row order)*

| Row | Panel Component | Hook |
|---|---|---|
| 1 | `OverviewMetrics.jsx` | `useMetrics.js` |
| 2 | `SentimentTrend.jsx` | `useSentimentTrend.js` |
| 2 | `TopicDistribution.jsx` | `useTopics.js` |
| 3 | `NarrativeShift.jsx` | `useNarrative.js` |
| 3 | `MisinfoAlerts.jsx` | `useArticles.js` |
| 4 | `LatestArticles.jsx` | `useArticles.js` |
| 4 | `SourceSentiment.jsx` | `useSources.js` |
| 5 | `TopEntities.jsx` | `useEntities.js` |
| 5 | `TrendingKeywords.jsx` | `useKeywords.js` |

### Layout

```
layout/Dashboard.jsx   # composes all panels into the 5-row grid
layout/Navbar.jsx      # app header
```

**Done when:** All 9 panels render real data from the API. The dashboard loads without errors and updates when new data arrives.  
**Depends on:** Module 7 (API)

---

## Module Dependency Order

```
Module 1 (Database)
    â†“
Module 2 (Config)
    â†“
Module 3 (Ingestion) â”€â”€â†’ Module 4 (NLP) â”€â”€â†’ Module 5 (Aggregator)
                                                    â†“
                         Module 6 (Scheduler) â†â”€â”€â”€â”€â”˜
                                â†“
                         Module 7 (API)
                                â†“
                         Module 8 (Frontend)
```

> **Key Rule:** Before moving to the next module, the current one must work in isolation. Don't connect two modules together until both work independently.

---

## Package Requirements

> Using `uv` for virtual environment management.

### Module 1 — Database & Schema

| Package | Reason |
|---|---|
| `supabase` | Supabase Python SDK for database access via REST API |
| `sqlalchemy` | ORM table definitions retained as schema reference |
| `psycopg2-binary` | PostgreSQL driver (used by migration script only) |

### Module 2 — Configuration & Settings

| Package | Reason |
|---|---|
| `python-dotenv` | Loads `.env` file into environment variables |
| `pydantic` | Settings validation and type checking |
| `pydantic-settings` | Extends pydantic specifically for settings management |

### Module 3 — Ingestion Pipeline

| Package | Reason |
|---|---|
| `feedparser` | Parses RSS and Atom XML feeds — handles malformed feeds gracefully |
| `requests` | HTTP calls to NewsAPI |
| `trafilatura` | Full text extraction (faster and more accurate than `newspaper3k`) |
| `httpx` | Async HTTP client, optional, faster for bulk fetching |
| `newsapi-python` | Official NewsAPI Python client |
| `beautifulsoup4` | Fallback HTML parser if trafilatura fails |
| `lxml` | Faster XML/HTML parser used by feedparser and beautifulsoup4 |

### Module 4 — NLP Pipeline

| Package | Reason |
|---|---|
| `spacy` | NER, tokenization, sentence segmentation |
| `en_core_web_sm` | spaCy English model — right balance of speed and accuracy |
| `transformers` | HuggingFace transformers library |
| `torch` | PyTorch backend required by HuggingFace |
| `keybert` | KeyBERT keyphrase extraction |
| `sentence-transformers` | Required by KeyBERT for semantic embeddings (~90MB on first run) |

**HuggingFace models:**

| Task | Model |
|---|---|
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` |
| Topic (zero-shot) | `facebook/bart-large-mnli` |
| Misinformation | `mrm8488/bert-tiny-finetuned-fake-news-detection` |

All free, open weights, no API key needed. Download automatically on first use.

> Install the spaCy language model separately after pip install:
> ```bash
> python -m spacy download en_core_web_sm
> ```

### Module 5 — Aggregator

| Package | Reason |
|---|---|
| `scikit-learn` | `TfidfVectorizer` — no need to implement TF-IDF from scratch |
| `numpy` | Rolling average math for spike detection |
| `pandas` | Data manipulation (optional) |

### Module 6 — Scheduler

| Package | Reason |
|---|---|
| `apscheduler` | Job scheduling inside FastAPI |

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
```

### Module 7 — REST API

| Package | Reason |
|---|---|
| `fastapi` | API framework |
| `uvicorn` | ASGI server that runs FastAPI |
| `python-multipart` | Required by FastAPI for form data handling (install explicitly) |

### Module 8 — Frontend Dashboard

| Package | Reason |
|---|---|
| `react` | UI framework |
| `react-dom` | React DOM renderer |
| `recharts` | Charting library built on React |
| `axios` | HTTP client (cleaner error handling than raw `fetch`) |
| `date-fns` | Lightweight date formatting and manipulation |
| `tailwindcss` | Utility CSS classes for layout and styling |

---

## Complete Backend `requirements.txt`

```txt
# Database (Supabase)
supabase>=2.0.0
sqlalchemy==2.0.23     # retained as schema reference
psycopg2-binary==2.9.9 # used by migration script only

# Configuration
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Ingestion
feedparser==6.0.10
requests==2.31.0
trafilatura==1.6.4
httpx==0.25.2
newsapi-python==0.2.7
beautifulsoup4==4.12.2
lxml==4.9.3

# NLP
spacy==3.7.2
transformers==4.36.0
torch==2.1.1          # see note below — install CPU version explicitly
keybert==0.8.3
sentence-transformers==2.2.2

# Aggregator
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.3

# Scheduler
apscheduler==3.10.4

# API
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
```

> **Important — PyTorch CPU version:**  
> `torch` without a specific index URL installs the full CUDA GPU version (~700MBâ€“2GB). For a local prototype, install the CPU version:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> ```

---

## Complete Frontend `package.json` Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "recharts": "^2.10.1",
    "axios": "^1.6.2",
    "date-fns": "^2.30.0",
    "tailwindcss": "^3.3.6"
  }
}
```
