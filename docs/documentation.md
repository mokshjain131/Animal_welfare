# Development Plan — Animal Welfare News Sentiment Tracker

## Guiding Principles

- **Simple functions** — each function does one thing, under ~30 lines
- **Basic functionality first** — get the pipeline working end-to-end before adding extras
- **Module isolation** — each module works and is testable on its own before connecting to the next
- **No premature optimization** — skip Redis, skip TimescaleDB, skip D3 for v1

---

## Build Order Overview

```
Module 1: Database & Schema          ← foundation, everything depends on this
Module 2: Configuration & Settings   ← all config in one place
Module 3: Ingestion Pipeline         ← articles flowing into the database
Module 4: NLP Pipeline               ← articles enriched with scores
Module 5: Aggregator                 ← summary tables populated
Module 6: Scheduler                  ← everything running automatically
Module 7: REST API                   ← endpoints serving data
Module 8: Frontend Dashboard         ← panels rendering real data
```

---

## Module 1 — Database & Schema ✅

**Goal:** PostgreSQL running, all tables created, connection working.  
**Status:** Complete and verified.

### Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | PostgreSQL 16 container (for future Docker use) |
| `backend/db/database.py` | Engine, session factory, FastAPI dependency, table creation |
| `backend/db/models.py` | 9 SQLAlchemy ORM models with relationships |
| `backend/db/migrations/init.sql` | Raw SQL mirror of models (Docker entrypoint) |
| `.env` / `.env.example` | Database connection string |

### Setup

- PostgreSQL 16 installed locally as a Windows service (`postgresql-x64-16`)
- Database `sentiment_tracker` created with user `postgres` / password `password`
- All 9 tables created via `init.sql` and verified with SQLAlchemy

---

### File: `backend/db/database.py`

Uses lazy singleton pattern — engine and session factory are created once on first use and cached in module-level globals.

#### `get_engine()`

```
Input  : None (reads DATABASE_URL from config.settings)
Output : sqlalchemy.Engine
```

Creates a SQLAlchemy engine connected to PostgreSQL. Uses `pool_pre_ping=True` to validate connections before use. Only created once — subsequent calls return the cached engine.

#### `get_session_factory()`

```
Input  : None
Output : sqlalchemy.orm.sessionmaker
```

Returns a session factory bound to the engine. Sessions are created with `autocommit=False, autoflush=False` for explicit transaction control.

#### `get_db()`

```
Input  : None
Output : Generator[Session] (yields a SQLAlchemy Session)
```

FastAPI dependency injection function. Yields a database session for the duration of an API request, then closes it in a `finally` block. Used as `db: Session = Depends(get_db)` in route functions.

#### `create_all_tables()`

```
Input  : None
Output : None
```

Calls `Base.metadata.create_all()` to create all tables defined in `models.py` if they don't already exist. Called once at application startup. Idempotent — safe to run multiple times.

---

### File: `backend/db/models.py`

All models inherit from `Base = declarative_base()`. Timestamps use `datetime.now(timezone.utc)` via the `_utcnow()` helper.

#### `Article` — table: `articles`

The core table. Every other table references this via `article_id` foreign key.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | |
| `url` | String(2048) | Unique, not null | Used for deduplication |
| `title` | Text | Not null | |
| `full_text` | Text | Nullable | Empty if scraping failed |
| `source_name` | String(255) | Not null | e.g. "BBC", "Reuters" |
| `source_type` | String(50) | Not null | `"rss"` or `"newsapi"` |
| `published_at` | DateTime | Not null | When the article was published |
| `created_at` | DateTime | Default: `utcnow` | When we ingested it |
| `is_processed` | Boolean | Default: `False` | `True` after NLP pipeline runs |

**Relationships:** `sentiment` (one-to-one), `topic` (one-to-one), `entities` (one-to-many), `keyphrases` (one-to-many), `flagged` (one-to-one)

#### `SentimentScore` — table: `sentiment_scores`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `article_id` | Integer | FK → `articles.id` |
| `label` | String(20) | `"positive"`, `"negative"`, or `"neutral"` |
| `score` | Float | Confidence score 0–1 |
| `created_at` | DateTime | Default: `utcnow` |

One row per article. Back-references `article`.

#### `TopicClassification` — table: `topics`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `article_id` | Integer | FK → `articles.id` |
| `topic` | String(100) | e.g. `"factory_farming"`, `"wildlife"` |
| `confidence` | Float | Classification confidence 0–1 |
| `created_at` | DateTime | Default: `utcnow` |

One row per article. Back-references `article`.

#### `Entity` — table: `entities`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `article_id` | Integer | FK → `articles.id` |
| `entity_text` | String(500) | e.g. `"WWF"`, `"United Kingdom"` |
| `entity_type` | String(50) | `"ORG"`, `"GPE"`, or `"ANIMAL"` |
| `created_at` | DateTime | Default: `utcnow` |

Multiple rows per article. Back-references `article`.

#### `FlaggedArticle` — table: `flagged_articles`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `article_id` | Integer | FK → `articles.id`, unique |
| `suspicion_score` | Float | Misinfo confidence 0–1 |
| `flag_reason` | String(500) | Nullable explanation |
| `is_reviewed` | Boolean | Default: `False` |
| `is_confirmed` | Boolean | Nullable — analyst decision |
| `created_at` | DateTime | Default: `utcnow` |
| `reviewed_at` | DateTime | Nullable |

One row per flagged article. `is_reviewed` and `is_confirmed` support the analyst review workflow.

#### `Keyphrase` — table: `keyphrases`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `article_id` | Integer | FK → `articles.id` |
| `phrase` | String(500) | Extracted keyphrase |
| `relevance_score` | Float | KeyBERT relevance 0–1 |
| `created_at` | DateTime | Default: `utcnow` |

Multiple rows per article (typically 3–5). Input to TF-IDF aggregator.

#### `TrendingKeyword` — table: `trending_keywords`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `phrase` | String(500) | Trending phrase |
| `score` | Float | TF-IDF spike score |
| `article_count` | Integer | Articles containing this phrase |
| `trend_direction` | String(10) | `"up"`, `"down"`, or `"new"` |
| `topic` | String(100) | Nullable topic category |
| `computed_at` | DateTime | Default: `utcnow` |

Overwritten entirely every 30 minutes by the aggregator.

#### `DailySummary` — table: `daily_summaries`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `date` | Date | Not null |
| `topic` | String(100) | Not null |
| `article_count` | Integer | Total articles for this topic on this date |
| `avg_sentiment` | Float | Average sentiment score |
| `positive_count` | Integer | Count of positive articles |
| `negative_count` | Integer | Count of negative articles |
| `neutral_count` | Integer | Count of neutral articles |
| `created_at` | DateTime | Default: `utcnow` |

**Unique constraint** on `(date, topic)` — one row per topic per day. Upserted by the aggregator.

#### `SpikeEvent` — table: `spike_events`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `topic` | String(100) | Which topic spiked |
| `spike_date` | Date | When the spike was detected |
| `article_count` | Integer | Count on the spike day |
| `weekly_avg` | Float | 7-day rolling average at time of detection |
| `multiplier` | Float | `article_count / weekly_avg` e.g. `2.1` |
| `is_active` | Boolean | Default: `True`, set `False` when spike subsides |
| `detected_at` | DateTime | Default: `utcnow` |

---

### File: `backend/db/migrations/init.sql`

Raw SQL version of all 9 tables with `CREATE TABLE IF NOT EXISTS` statements. Mounted into Docker container as `/docker-entrypoint-initdb.d/init.sql` for automatic initialization.

**Indexes created:**
- `articles.url` — unique index for O(1) deduplication lookups
- `articles.published_at` — time-range queries
- `articles.is_processed` — NLP pipeline queries for unprocessed articles
- `sentiment_scores.article_id` — join lookups
- `topics.topic` — topic filtering
- `entities.article_id` — join lookups
- `keyphrases.article_id` — join lookups
- `daily_summaries(date, topic)` — composite index for rollup queries
- `spike_events.is_active` — active spike lookups

### Verification

Verified by `tests/verify_module1.py`:
1. Engine connects to PostgreSQL ✅
2. `create_all_tables()` runs without error ✅
3. Insert a test `Article` row, read it back, delete it ✅
4. All 9 tables confirmed via `psql \dt` ✅

---

## Module 2 — Configuration & Settings ✅

**Goal:** All config values loaded from `.env`, keyword lists defined, importable everywhere.  
**Status:** Complete and verified.

### Files

| File | Purpose |
|---|---|
| `backend/config/settings.py` | Pydantic `BaseSettings` class — loads `.env`, validates types |
| `backend/config/keywords.py` | 6 topic categories, 65 keywords, 3 helper functions |
| `.env.example` | Template with all config fields documented |

---

### File: `backend/config/settings.py`

Uses `pydantic_settings.BaseSettings` which automatically reads environment variables from `.env` and validates their types at import time. If a required variable is missing or has the wrong type, the app fails at startup with a clear error.

#### `Settings` class

| Field | Type | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | `str` | `postgresql://postgres:password@localhost:5432/sentiment_tracker` | PostgreSQL connection string |
| `NEWSAPI_KEY` | `str` | `""` | NewsAPI.org API key |
| `RSS_FEEDS` | `list[str]` | 4 feed URLs (BBC, Guardian, NYT, Al Jazeera) | RSS feeds to monitor |
| `MISINFO_THRESHOLD` | `float` | `0.65` | Score above which an article is flagged for review |
| `FALLBACK_TEXT_LENGTH` | `int` | `150` | If scraped text is shorter than this, use title + description instead |
| `KEYBERT_TOP_N` | `int` | `5` | Number of keyphrases to extract per article |
| `TRENDING_KEYWORDS_TOP_N` | `int` | `10` | Number of trending phrases shown on dashboard |
| `SPIKE_MULTIPLIER` | `float` | `2.0` | Topic must exceed this multiple of weekly average to trigger spike |
| `PIPELINE_INTERVAL_MINUTES` | `int` | `30` | How often the ingestion + NLP pipeline runs |
| `APP_ENV` | `str` | `"development"` | Environment name |
| `LOG_LEVEL` | `str` | `"INFO"` | Logging verbosity |

**Usage from any module:**
```python
from config.settings import settings
# settings.DATABASE_URL, settings.MISINFO_THRESHOLD, etc.
```

---

### File: `backend/config/keywords.py`

#### `TOPIC_KEYWORDS` (dict)

A dictionary mapping 6 topic categories to their keyword lists (65 keywords total):

| Topic | Keywords | Count |
|---|---|---|
| `factory_farming` | factory farm, battery cage, gestation crate, slaughterhouse, broiler, … | 13 |
| `animal_testing` | animal testing, vivisection, lab animals, cosmetics testing, … | 9 |
| `wildlife` | wildlife, poaching, ivory trade, endangered species, trophy hunting, … | 14 |
| `pet_welfare` | animal cruelty, dog fighting, puppy mill, animal hoarding, … | 11 |
| `animal_policy` | animal welfare law, animal rights bill, animal protection act, … | 8 |
| `veganism` | vegan, plant-based, meat industry, dairy industry, cruelty-free food, … | 10 |

#### `get_all_keywords()`

```
Input  : None
Output : list[str] — flat list of all 65 keywords across all topics
```

Flattens `TOPIC_KEYWORDS.values()` into a single list. Used by the Relevance Gate for a quick any-match check before running NLP.

#### `get_topic_labels()`

```
Input  : None
Output : list[str] — ["factory_farming", "animal_testing", "wildlife", "pet_welfare", "animal_policy", "veganism"]
```

Returns the topic category names. Used as candidate labels for HuggingFace zero-shot classification.

#### `detect_topic_from_keywords(text)`

```
Input  : text: str — article full_text or title
Output : str | None — topic name with the most keyword matches, or None if no matches
```

Simple fallback topic detection by keyword counting. For each topic, counts how many of its keywords appear in the lowercased text. Returns the topic with the highest count, or `None` if zero matches.

Used as a fallback when the HuggingFace topic classifier is unavailable or too slow.

### Verification

Verified by `tests/verify_module2.py`:
1. `settings.DATABASE_URL` reads correctly from `.env` ✅
2. All 11 settings fields have correct types and defaults ✅
3. `get_all_keywords()` returns 65 keywords ✅
4. `get_topic_labels()` returns 6 topics ✅
5. `detect_topic_from_keywords("factory farming investigation")` → `"factory_farming"` ✅
6. `detect_topic_from_keywords("poaching elephants in Africa")` → `"wildlife"` ✅
7. `detect_topic_from_keywords("vegan plant-based diet")` → `"veganism"` ✅
8. `detect_topic_from_keywords("random unrelated text about weather")` → `None` ✅
9. Database engine still connects correctly ✅

---

## Module 3 — Ingestion Pipeline ✅

**Goal:** Articles fetched from RSS and NewsAPI, scraped for full text, normalized, deduplicated, and filtered for relevance. Saved to `articles` table.  
**Status:** Complete and verified.

### Files

| File | Purpose |
|---|---|
| `backend/ingestion/rss_fetcher.py` | Parse RSS feeds via feedparser |
| `backend/ingestion/newsapi_fetcher.py` | Query NewsAPI via plain requests |
| `backend/ingestion/scraper.py` | Extract full text via trafilatura |
| `backend/ingestion/normalizer.py` | Merge all sources into standard schema |
| `backend/ingestion/deduplicator.py` | URL-based dedup against DB + batch |
| `backend/ingestion/relevance_gate.py` | Keyword-based animal welfare filter |

### Dependencies Installed

- `feedparser 6.0.12` — RSS/Atom feed parsing
- `requests 2.32.5` — HTTP client for NewsAPI
- `trafilatura 2.0.0` — article full-text extraction (includes lxml, courlan, htmldate)
- `python-dateutil 2.9.0` — flexible date parsing for normalizer

### Standard Article Schema (output of this module)

```python
{
    "title":        str,
    "full_text":    str,
    "source_name":  str,
    "url":          str,
    "published_at": datetime,
    "source_type":  "rss" | "newsapi"
}
```

---

### File: `backend/ingestion/rss_fetcher.py`

#### `fetch_rss_feed(feed_url)`

```
Input  : feed_url: str — a single RSS feed URL
Output : list[dict] — raw article dicts with keys: title, url, description, source_name, published_at
Error  : returns [] on any exception (logged)
```

Calls `feedparser.parse(feed_url)`. If `feed.bozo` is set and there are no entries, logs a warning and returns empty. Otherwise iterates `feed.entries` extracting title, link, summary, and published date. Parses dates from `published_parsed` or `updated_parsed` via `time.mktime` → `datetime.fromtimestamp`, falling back to `datetime.now(utc)`.

#### `fetch_all_rss_feeds()`

```
Input  : None (reads settings.RSS_FEEDS — 4 feeds by default)
Output : list[dict] — combined raw articles from all configured feeds
```

Loops over each feed URL in `settings.RSS_FEEDS`, calls `fetch_rss_feed()`, extends a combined list, logs the total count.

---

### File: `backend/ingestion/newsapi_fetcher.py`

Uses plain `requests.get()` against `https://newsapi.org/v2/everything` (no SDK dependency).

#### `fetch_newsapi_articles(query, page_size=20)`

```
Input  : query: str — search string, e.g. "factory farm OR battery cage"
         page_size: int — max results per request (default 20)
Output : list[dict] — article dicts with keys: title, url, description, source_name, published_at
Error  : returns [] if NEWSAPI_KEY is empty, on HTTP error, or on invalid response
```

Sends GET request with params `q`, `language=en`, `sortBy=publishedAt`, `pageSize`, `apiKey`. Checks `status == "ok"` in response JSON, parses `publishedAt` via `datetime.fromisoformat()`, extracts `source.name`.

#### `fetch_all_newsapi_articles()`

```
Input  : None (reads TOPIC_KEYWORDS and settings.NEWSAPI_KEY)
Output : list[dict] — combined articles from all 6 topic queries
```

For each topic in `TOPIC_KEYWORDS`, joins the first 3 keywords with `" OR "` to build a query string, calls `fetch_newsapi_articles()`. Skips entirely if `NEWSAPI_KEY` is empty.

> **API quota**: Free tier = 100 requests/day. With 6 topics per run, budget ~16 runs/day. In Module 6, NewsAPI will run less frequently than RSS.

---

### File: `backend/ingestion/scraper.py`

#### `scrape_full_text(url)`

```
Input  : url: str — article URL
Output : str | None — extracted text, or None if failed / too short
```

Calls `trafilatura.fetch_url(url)` to download, then `trafilatura.extract(downloaded)` to strip boilerplate. Returns `None` if download fails, extraction fails, or extracted text is shorter than `settings.FALLBACK_TEXT_LENGTH` (150 chars).

#### `enrich_with_full_text(articles)`

```
Input  : articles: list[dict] — must have 'url', 'title', 'description' keys
Output : list[dict] — same list with 'full_text' key added to every article
```

For each article, calls `scrape_full_text()`. If successful, sets `full_text` to the extracted text. If `None`, falls back to `title + ". " + description`. Sleeps 1 second between requests to avoid rate limiting. Logs how many got full scrapes vs fallbacks.

---

### File: `backend/ingestion/normalizer.py`

Uses `python-dateutil.parser.parse()` for flexible date string handling.

#### `normalize_article(raw, source_type)`

```
Input  : raw: dict — raw article from any fetcher
         source_type: str — "rss" or "newsapi"
Output : dict | None — normalized article dict, or None if URL is invalid
```

Strips/truncates title (max 1000 chars). Validates URL starts with `http`. Parses `published_at` — accepts datetime objects or strings (via `dateutil.parser.parse`), falls back to `datetime.now(utc)`. Ensures timezone awareness. Returns standard schema dict.

#### `normalize_all(rss_articles, newsapi_articles)`

```
Input  : rss_articles: list[dict] — from RSS fetcher
         newsapi_articles: list[dict] — from NewsAPI fetcher
Output : list[dict] — combined list of normalized articles (invalid ones filtered out)
```

Normalizes each RSS article with `source_type="rss"`, each NewsAPI article with `source_type="newsapi"`, combines into one list.

---

### File: `backend/ingestion/deduplicator.py`

#### `get_existing_urls(db)`

```
Input  : db: Session — SQLAlchemy session
Output : set[str] — all article URLs currently in the database
```

Single query: `db.query(Article.url).all()` → set comprehension. O(1) lookup for each incoming article.

#### `deduplicate(articles, db)`

```
Input  : articles: list[dict] — normalized articles (must have 'url')
         db: Session — SQLAlchemy session
Output : list[dict] — articles with DB duplicates and batch duplicates removed
```

Fetches existing URLs, maintains a `seen_in_batch` set, skips any article whose URL is in either set. Logs kept vs dropped counts.

---

### File: `backend/ingestion/relevance_gate.py`

#### `is_relevant(article)`

```
Input  : article: dict — must have 'title' and 'full_text' keys
Output : bool — True if any animal welfare keyword found in title + full_text
```

Combines `title + full_text`, lowercases, checks each keyword from `get_all_keywords()` (65 keywords). Returns `True` on first match, `False` if no match.

#### `filter_relevant(articles)`

```
Input  : articles: list[dict] — normalized articles
Output : (relevant: list[dict], rejected: list[dict])
```

Splits articles into two lists. Logs counts for both groups.

---

### Settings Fix

Updated `backend/config/settings.py` to resolve `.env` from the project root using `Path(__file__).resolve().parent.parent.parent / ".env"` instead of relative `".env"`. This ensures settings load correctly regardless of the working directory.

### Verification

Verified by `tests/verify_module3.py`:
1. RSS fetcher: 110 articles from 4 feeds (BBC, Guardian, NYT, Al Jazeera) ✅
2. NewsAPI fetcher: graceful degradation when key is invalid (returns `[]`, logs error) ✅
3. Scraper: trafilatura extracts 6000+ chars from BBC/Guardian articles ✅
4. Normalizer: 110 articles merged with standard 6-key schema ✅
5. Deduplicator: catches already-saved URLs, drops batch duplicates ✅
6. Relevance gate: 4 relevant articles from 110 general news (expected for environment feeds) ✅
7. DB save: 4 articles persisted in `articles` table with `is_processed=False` ✅
8. Re-run dedup: correctly catches all previously saved URLs ✅

> **Note:** NewsAPI key provided was invalid (UUID format — NewsAPI uses 32-char hex keys). Update the `NEWSAPI_KEY` in `.env` with a valid key from https://newsapi.org. The fetcher degrades gracefully — returns empty list when key is missing or invalid.

---

## Module 4 — NLP Pipeline ✅

**Goal:** Each article is enriched with sentiment, topic, entities, keyphrases, and misinfo flag.  
**Status:** Complete and verified.

### Files

| File | Purpose |
|---|---|
| `backend/nlp/spacy_processor.py` | NER entity extraction + text cleaning (spaCy) |
| `backend/nlp/sentiment.py` | Sentiment analysis (HuggingFace cardiffnlp) |
| `backend/nlp/topic_classifier.py` | Zero-shot topic classification (BART-MNLI) |
| `backend/nlp/misinfo_detector.py` | Misinformation suspicion scoring (bert-tiny) |
| `backend/nlp/keybert_extractor.py` | Keyphrase extraction (KeyBERT + sentence-transformers) |
| `backend/nlp/pipeline.py` | Orchestrator — calls all above, saves to DB |

### Dependencies Installed

- `spacy 3.8.11` + `en_core_web_sm 3.8.0` — NER and text processing
- `transformers 5.3.0` — HuggingFace inference pipelines
- `torch 2.10.0` — PyTorch backend for transformers
- `keybert 0.9.0` + `sentence-transformers 5.2.3` — keyphrase extraction
- `scikit-learn 1.8.0` — dependency of KeyBERT

### Models

| Task | Model | Size | First-load Download |
|---|---|---|---|
| NER + cleaning | spaCy `en_core_web_sm` | ~12MB | Installed via URL |
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` | ~500MB | Auto-cached by HuggingFace |
| Topic (zero-shot) | `facebook/bart-large-mnli` | ~1.6GB | Auto-cached by HuggingFace |
| Misinfo | `mrm8488/bert-tiny-finetuned-fake-news-detection` | ~17MB | Auto-cached by HuggingFace |
| Keyphrases | `all-MiniLM-L6-v2` (via KeyBERT) | ~90MB | Auto-cached by HuggingFace |

All models are loaded once at first use and cached in module-level globals. Subsequent calls reuse the cached model.

---

### File: `backend/nlp/spacy_processor.py`

Contains a predefined `ANIMAL_TERMS` set (40+ terms: pig, chicken, cow, elephant, dolphin, whale, tiger, etc.) and `ALLOWED_LABELS = {"ORG", "GPE", "LOC"}` for spaCy NER filtering.

#### `load_spacy_model()`

```
Input  : None
Output : spacy.Language — the en_core_web_sm model
```

Loads `spacy.load("en_core_web_sm")` once and caches in `_nlp` global. All subsequent calls return the cached model.

#### `extract_entities(text, nlp)`

```
Input  : text: str — article text (capped at 100k chars)
         nlp: Language — spaCy model
Output : list[dict] — each dict has "entity_text" and "entity_type" ("ORG", "GPE", or "ANIMAL")
```

1. Runs `nlp(text)` to get the spaCy Doc
2. Extracts entities where `label_` is ORG, GPE, or LOC (LOC mapped to GPE)
3. Checks `ANIMAL_TERMS` against lowercased text for custom ANIMAL entities
4. Deduplicates by `(text, type)` pair

#### `clean_text(text, nlp)`

```
Input  : text: str — raw article text (capped at 100k chars)
         nlp: Language — spaCy model
Output : str — text with punctuation-only and whitespace-only tokens removed
```

Runs `nlp(text)`, filters out `token.is_punct` and `token.is_space`, rejoins remaining tokens.

#### `process_article(text)`

```
Input  : text: str — article full_text
Output : {"cleaned_text": str, "entities": list[dict]}
```

Main entry point. Calls `load_spacy_model()`, then `extract_entities()` and `clean_text()`, returns both results.

---

### File: `backend/nlp/sentiment.py`

Uses `_LABEL_MAP` dict to normalize model labels (handles both named labels like "positive" and LABEL_0/1/2 format).

#### `load_sentiment_model()`

```
Input  : None
Output : HuggingFace pipeline (sentiment-analysis)
```

Loads `cardiffnlp/twitter-roberta-base-sentiment-latest` with `truncation=True, max_length=512`. Cached in `_sentiment_model` global.

#### `analyze_sentiment(text)`

```
Input  : text: str — cleaned article text (first 512 chars used)
Output : {"label": "positive"|"negative"|"neutral", "score": float 0-1}
Error  : returns {"label": "neutral", "score": 0.0}
```

Runs the model, maps the raw label to lowercase standard via `_LABEL_MAP`, rounds score to 4 decimal places.

---

### File: `backend/nlp/topic_classifier.py`

#### `load_topic_model()`

```
Input  : None
Output : HuggingFace pipeline (zero-shot-classification)
```

Loads `facebook/bart-large-mnli` with `truncation=True`. Cached in `_topic_model` global. This is the largest model (~1.6GB).

#### `classify_topic(text)`

```
Input  : text: str — cleaned article text (first 500 chars used)
Output : {"topic": str, "confidence": float 0-1}
Error  : falls back to detect_topic_from_keywords(text), then "unknown"
```

1. Converts topic labels to human-readable (e.g. "factory_farming" → "factory farming") for better zero-shot results
2. Runs model with candidate_labels from `get_topic_labels()`
3. Takes top label and score, converts back to snake_case
4. On any error, falls back to Module 2's keyword-based `detect_topic_from_keywords()`

---

### File: `backend/nlp/misinfo_detector.py`

#### `load_misinfo_model()`

```
Input  : None
Output : HuggingFace pipeline (text-classification)
```

Loads `mrm8488/bert-tiny-finetuned-fake-news-detection` with `truncation=True, max_length=512`. Tiny model (~17MB).

#### `score_misinfo(text)`

```
Input  : text: str — cleaned article text (first 512 chars used)
Output : {
    "suspicion_score": float 0-1,
    "should_flag": bool,
    "flag_reason": str
}
Error  : returns suspicion_score=0.0, should_flag=False
```

1. Model returns FAKE or REAL label with confidence
2. If FAKE: `suspicion_score = confidence`
3. If REAL: `suspicion_score = 1 - confidence`
4. `should_flag = suspicion_score >= settings.MISINFO_THRESHOLD` (default 0.65)
5. Flag reason is always "Flagged for review — model detected potentially misleading content"

> Never describes output as "confirmed misinformation" — it is a suspicion score for human review.

---

### File: `backend/nlp/keybert_extractor.py`

#### `load_keybert_model()`

```
Input  : None
Output : KeyBERT instance (uses all-MiniLM-L6-v2 under the hood)
```

Creates `KeyBERT()` once and caches in `_keybert_model` global.

#### `extract_keyphrases(text)`

```
Input  : text: str — cleaned article text (must be ≥50 chars)
Output : list[dict] — each dict has "phrase" and "relevance_score" (0-1)
Error  : returns [] if text too short or on any failure
```

Calls `model.extract_keywords(text, keyphrase_ngram_range=(1,3), stop_words="english", top_n=settings.KEYBERT_TOP_N)`. Returns top 5 keyphrases by default.

---

### File: `backend/nlp/pipeline.py`

The orchestrator. Calls all NLP functions in sequence and writes results to the database.

#### `process_article(article, db)`

```
Input  : article: Article — SQLAlchemy Article row (must have id, full_text)
         db: Session — SQLAlchemy session
Output : None (writes to 5 tables: entities, sentiment_scores, topics, flagged_articles, keyphrases)
```

Pipeline steps:
1. **spaCy** → `process_article(text)` → saves entities to `entities` table
2. **Sentiment** → `analyze_sentiment(cleaned_text)` → saves to `sentiment_scores`
3. **Topic** → `classify_topic(cleaned_text)` → saves to `topics`
4. **Misinfo** → `score_misinfo(cleaned_text)` → saves to `flagged_articles` only if `should_flag=True`
5. **KeyBERT** → `extract_keyphrases(cleaned_text)` → saves to `keyphrases`
6. **Mark processed** → sets `article.is_processed = True`

Error handling: wraps entire pipeline in try/except. On failure, logs error but still marks article as processed to avoid infinite retries.

#### `process_unprocessed_articles(db)`

```
Input  : db: Session — SQLAlchemy session
Output : int — number of articles processed
```

1. Queries `articles` where `is_processed=False`
2. For each article: calls `process_article()`, commits after each
3. Logs progress every 10 articles
4. Returns total count

---

### Verification

Verified by `tests/verify_module4.py`:

**Individual component tests:**
1. spaCy: extracted 8 entities (ORG: "WWF", GPE: "UK", "London", "Europe", ANIMAL: "chicken", "chickens", "pig", "pigs") ✅
2. Sentiment: positive text → "positive" (0.9879), negative → "negative" (0.9437), neutral → "neutral" (0.9227) ✅
3. Topic: "factory farming battery cage" → factory_farming (0.9299), "vegan restaurant" → veganism (0.7898), "elephant poaching" → wildlife (0.9593) ✅
4. Misinfo: suspicion_score=0.0133, should_flag=False (correct — legitimate test text) ✅
5. KeyBERT: 5 keyphrases extracted with relevance scores 0.54–0.62 ✅

**Full pipeline on DB articles:**
6. Processed 6 unprocessed articles from DB ✅
7. `sentiment_scores`: 6 rows ✅
8. `topics`: 6 rows ✅
9. `entities`: 28 rows ✅
10. `keyphrases`: 20 rows ✅
11. `flagged_articles`: 0 rows (no articles exceeded misinfo threshold) ✅
12. All 6 articles marked `is_processed=True` ✅

---

## Module 5 — Aggregator

**Status:** ✅ Complete  
**Files:** `backend/aggregator/daily_summary.py`, `tfidf_keywords.py`, `spike_detector.py`

### Implementation

Three aggregator files compute pre-aggregated data so the dashboard reads fast. All are idempotent — running twice produces the same result, never duplicates.

---

### File: `backend/aggregator/daily_summary.py`

#### `_compute_summary_for_date(target_date, db)`

```
Input  : target_date: date, db: Session
Output : int — number of summary rows upserted
```

1. For each topic in `get_topic_labels()`:
   - Joins `articles` ↔ `topics` ↔ `sentiment_scores` for the given date range
   - Computes: total count, avg sentiment, positive/negative/neutral counts
   - Uses `func.cast(SentimentScore.label == "positive", Integer)` for counting by label
   - Upsert: deletes existing row for `(date, topic)`, then inserts fresh row
2. Commits once after all topics

#### `compute_daily_summaries(db)`

```
Input  : db: Session
Output : None
```

Calls `_compute_summary_for_date()` for today's date.

#### `compute_historical_summaries(db, days_back=30)`

```
Input  : db: Session, days_back: int (default 30)
Output : None
```

Loops from `days_back` days ago to today, calling `_compute_summary_for_date()` for each. Used once at setup to backfill history.

---

### File: `backend/aggregator/tfidf_keywords.py`

#### `_get_phrase_counts(db, since)`

```
Input  : db: Session, since: datetime
Output : Counter — keyphrase → occurrence count
```

Joins `keyphrases` ↔ `articles`, filters by `published_at >= since`, lowercases all phrases.

#### `compute_trending_keywords(db)`

```
Input  : db: Session
Output : None
```

1. Fetches keyphrase counts for last 24 hours (`today_counts`) and last 7 days (`baseline_counts`)
2. For each phrase in today's set:
   - `baseline_avg = baseline_total / 7`
   - `spike_score = today_count / max(baseline_avg, 1)`
   - Trend: `"new"` (not in baseline), `"up"` (>1.5×), `"down"` (<0.5×), `"stable"`
3. Sorts by spike_score descending, takes top `TRENDING_KEYWORDS_TOP_N` (default 10)
4. Deletes all existing `trending_keywords` rows, inserts new top phrases
5. Commits

---

### File: `backend/aggregator/spike_detector.py`

#### `compute_weekly_average(topic, db)`

```
Input  : topic: str, db: Session
Output : float — avg daily article count over past 7 days
```

Queries `daily_summaries` for `topic` where `date` is within past 7 days (excluding today). Sums `article_count` and divides by 7.

#### `detect_spikes(db)`

```
Input  : db: Session
Output : list[dict] — newly detected spikes
```

1. For each topic in `get_topic_labels()`:
   - Gets today's count from `daily_summaries`
   - Computes `multiplier = today_count / max(weekly_avg, 1)`
   - If `multiplier >= SPIKE_MULTIPLIER` (2.0): inserts new `spike_events` row (skips if already exists for today)
   - Otherwise: sets `is_active=False` on any active spike for this topic
2. Commits, returns list of new spikes

#### `run_aggregator(db)`

```
Input  : db: Session
Output : None
```

Orchestrator — calls all three jobs in sequence:
1. `compute_daily_summaries(db)`
2. `compute_trending_keywords(db)`
3. `detect_spikes(db)`

Logs start/completion and spike count.

---

### Verification

Verified by `tests/verify_module5.py`:

1. **Daily summaries**: 4 rows written across historical dates ✅
   - `2026-03-09 | veganism | 1 article  | avg_sent=0.6885 | ~1`
   - `2026-03-08 | wildlife | 2 articles | avg_sent=0.7296 | ~2`
   - `2026-03-07 | wildlife | 1 article  | avg_sent=0.5955 | +1`
   - `2026-03-06 | wildlife | 1 article  | avg_sent=0.7776 | ~1`
2. **Trending keywords**: 0 phrases (no articles in last 24h — expected with older test data) ✅
3. **Weekly averages**: wildlife=0.57, veganism=0.14, others=0.00 ✅
4. **Spike detection**: 0 spikes (no articles today, so no volume anomaly) ✅
5. **Idempotency**: daily_summaries count unchanged after running aggregator twice (4 → 4) ✅

---

## Module 6 — Scheduler

**Status:** ✅ Complete  
**Files:** `backend/ingestion/scheduler.py`, `backend/main.py`  
**Dependencies installed:** `apscheduler==3.11.2`, `fastapi==0.135.1`, `uvicorn==0.41.0`, `starlette==0.52.1`

### Implementation

Two files that wire all backend modules together into one automated pipeline.

---

### File: `backend/ingestion/scheduler.py`

#### `run_ingestion_pipeline()`

```
Input  : None
Output : None (side effects: DB inserts, NLP processing, aggregation)
Error  : Catches all exceptions, logs traceback, never crashes
```

Executes the complete pipeline in sequence:

| Step | Action | Details |
|---|---|---|
| 1 | Fetch RSS | `fetch_all_rss_feeds()` — all 4 feeds |
| 2 | Fetch NewsAPI | `fetch_all_newsapi_articles()` — **only on even runs** (conserves API quota) |
| 3 | Enrich | `enrich_with_full_text()` — each source set separately |
| 4 | Normalize | `normalize_all(rss, newsapi)` — standardize schema |
| 5 | Deduplicate | `deduplicate(normalized, db)` — skip URLs already in DB |
| 6 | Filter | `filter_relevant(unique)` — keyword-based relevance gate |
| 7 | Save | Insert each relevant article as `is_processed=False` |
| 8 | NLP | `process_unprocessed_articles(db)` — sentiment, topic, entities, keyphrases, misinfo |
| 9 | Aggregate | `run_aggregator(db)` — daily summaries, trending keywords, spikes |
| 10 | Log | Elapsed time, article counts (fetched, saved, processed, rejected) |

- Uses module-level `_run_count` to track odd/even runs for NewsAPI quota management
- Entire function wrapped in try/except — failed runs log error but never crash the scheduler
- DB session created and closed within the function scope

#### `create_scheduler()`

```
Input  : None
Output : BackgroundScheduler — configured APScheduler instance
```

Creates a `BackgroundScheduler` with one `IntervalTrigger` job at `PIPELINE_INTERVAL_MINUTES` (30 min default). Returns the scheduler without starting it (started in `main.py`).

---

### File: `backend/main.py`

#### `lifespan(app)` (async context manager)

Replaces deprecated `@app.on_event("startup")`/`"shutdown"` pattern.

**Startup:**
1. `create_all_tables()` — ensures DB schema exists
2. `create_scheduler()` + `scheduler.start()` — starts APScheduler
3. `run_ingestion_pipeline()` — immediate initial run so dashboard has data

**Shutdown:**
- `scheduler.shutdown()` — clean stop

#### `create_app()`

```
Input  : None
Output : FastAPI app instance
```

1. Creates `FastAPI(title="Animal Welfare Sentiment Tracker", version="0.1.0")`
2. CORS middleware: allows `http://localhost:3000`, GET only
3. Router registration: 9 routers wrapped in `try/except ImportError` — gracefully skips routers not yet built (Module 7)
4. Health endpoint: `GET /health` → `{"status": "ok"}`

**Run command:** `uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000`

---

### Verification

Verified by `tests/verify_module6.py` + manual uvicorn startup:

1. **Import check**: `run_ingestion_pipeline`, `create_scheduler`, `create_app` all import correctly ✅
2. **Scheduler creation**: `BackgroundScheduler` with 1 job (`ingestion_pipeline`, interval trigger) ✅
3. **Pipeline run #1** (odd — skips NewsAPI):
   - Fetched 110 RSS articles, skipped NewsAPI
   - Saved 13 new articles, NLP processed 13
   - Aggregator ran (daily summaries, trending keywords, spike detection)
   - Completed in 226s ✅
4. **Pipeline run #2** (even — includes NewsAPI):
   - Fetched 110 RSS + 106 NewsAPI = 216 articles
   - After dedup: 194 unique, 30 relevant saved, 164 rejected
   - NLP processed 30 articles
   - Completed successfully ✅
5. **FastAPI app**: title correct, version 0.1.0, `/health` endpoint returns `{"status": "ok"}` ✅
6. **Uvicorn startup**: App boots, runs initial pipeline, serves health endpoint on port 8000 ✅
7. **DB state after verification**: 49 articles, all processed, 49 sentiments, 4 daily summaries ✅

---

## Module 7 — REST API

**Status:** ✅ Complete  
**Files:** 9 route files under `backend/api/routes/`

### Implementation

10 GET endpoints following a consistent pattern: `APIRouter` + `db: Session = Depends(get_db)` + query + return dict. Default date range is **7 days**, no pagination (returns all matching results with optional `limit`).

---

### `GET /overview/metrics` — [metrics.py](backend/api/routes/metrics.py)

Returns dashboard stat card values.

```json
{
  "articles_today": 0,
  "avg_sentiment": 0.0,
  "avg_sentiment_label": "negative|neutral|positive",
  "avg_sentiment_vs_yesterday": -0.7355,
  "active_topics": 2,
  "misinfo_alerts": 0,
  "active_spike": null | {"topic": "...", "multiplier": 2.1, "detected_at": "..."}
}
```

Logic: counts articles published today, computes avg sentiment today vs yesterday, counts distinct topics in daily_summaries (7 days), counts unreviewed flagged articles, finds most recent active spike.

---

### `GET /sentiment/trend` — [sentiment.py](backend/api/routes/sentiment.py)

| Param | Default | Description |
|---|---|---|
| `topic` | _(none)_ | Filter by topic |
| `days` | `7` | Lookback days |

Returns `{"data": [{"date", "avg_sentiment", "article_count", "topic"}]}` from `daily_summaries` table.

---

### `GET /topics/volume` — [topics.py](backend/api/routes/topics.py)

| Param | Default |
|---|---|
| `days` | `7` |

Returns `{"data": [{"topic", "article_count"}]}` — aggregated from `daily_summaries`, sorted by count desc.

---

### `GET /narrative/shifts` — [narrative.py](backend/api/routes/narrative.py)

| Param | Default |
|---|---|
| `days` | `14` |

Returns `{"dates": [...], "series": [{"topic", "values": [...]}]}` — time series per topic for area chart.

---

### `GET /articles/recent` — [articles.py](backend/api/routes/articles.py)

| Param | Default | Description |
|---|---|---|
| `limit` | `20` | Max articles |
| `topic` | _(none)_ | Filter by topic |
| `sentiment` | _(none)_ | `"positive"`, `"negative"`, `"neutral"` |
| `source` | _(none)_ | Source name (partial match) |

Joins `articles` ↔ `sentiment_scores` ↔ `topics`, checks `flagged_articles` for `is_flagged` boolean.

### `GET /articles/flagged` — [articles.py](backend/api/routes/articles.py)

| Param | Default |
|---|---|
| `limit` | `20` |

Returns unreviewed flagged articles ordered by `suspicion_score` desc.

---

### `GET /trending/keywords` — [keywords.py](backend/api/routes/keywords.py)

No params. Returns all rows from `trending_keywords` table ordered by score desc.

---

### `GET /entities/top` — [entities.py](backend/api/routes/entities.py)

| Param | Default |
|---|---|
| `days` | `7` |
| `limit` | `5` per type |

Returns `{"organizations": [...], "locations": [...], "animals": [...]}` — top N per entity type.

---

### `GET /spikes/active` — [spikes.py](backend/api/routes/spikes.py)

No params. Returns all active `spike_events` ordered by `detected_at` desc.

---

### `GET /sources/sentiment` — [sources.py](backend/api/routes/sources.py)

| Param | Default |
|---|---|
| `limit` | `10` |
| `days` | `7` |

Returns per-source article count and avg sentiment, with derived label. Sorted by volume desc.

---

### Verification

All 10 endpoints tested via `Invoke-RestMethod` against running uvicorn server:

| Endpoint | Status | Sample Data |
|---|---|---|
| `GET /health` | 200 ✅ | `{"status": "ok"}` |
| `GET /overview/metrics` | 200 ✅ | 2 active topics, 0 misinfo alerts |
| `GET /sentiment/trend` | 200 ✅ | 4 rows (wildlife × 3 days, veganism × 1) |
| `GET /topics/volume` | 200 ✅ | wildlife: 4, veganism: 1 |
| `GET /narrative/shifts` | 200 ✅ | 4 dates, 2 topic series |
| `GET /articles/recent` | 200 ✅ | 20 articles with sentiment + topic |
| `GET /articles/flagged` | 200 ✅ | 0 flagged (none above threshold) |
| `GET /trending/keywords` | 200 ✅ | 0 keywords (no articles today) |
| `GET /entities/top` | 200 ✅ | Top 5 orgs, locations, animals |
| `GET /spikes/active` | 200 ✅ | 0 active spikes |
| `GET /sources/sentiment` | 200 ✅ | 10 sources with avg sentiment |

**Query parameter tests:**
- `?topic=wildlife` — correctly filters sentiment trend to wildlife only ✅
- `?sentiment=positive&limit=3` — returns exactly 3 positive articles ✅
- `?days=30&limit=3` — entities endpoint correctly expands time range ✅

---

## Module 8 — Frontend Dashboard

**Goal:** 9 panels rendering real data from the API in a 5-row grid layout.

### Build Order

**Step 1: Foundation**
- `utils/api.js` — axios client with all fetch functions
- `utils/constants.js` — topic colors, sentiment colors, refresh interval
- `utils/formatters.js` — date formatting, score display, label prettifying

**Step 2: Shared Components**
- `SentimentBadge.jsx` — colored pos/neg/neutral tag
- `TopicBadge.jsx` — colored topic label
- `SpikeBanner.jsx` — red alert banner (renders nothing if no spike)
- `MisinfoFlag.jsx` — flag icon with tooltip
- `LoadingSpinner.jsx` — centered spinner

**Step 3: Hooks (one per API endpoint)**
- `useMetrics.js`, `useSentimentTrend.js`, `useTopics.js`, `useNarrative.js`
- `useArticles.js`, `useKeywords.js`, `useEntities.js`, `useSpikes.js`, `useSources.js`

**Step 4: Panels (build in row order)**

| Row | Panel | Chart Type |
|---|---|---|
| 1 | `OverviewMetrics.jsx` | 4 stat cards + spike banner |
| 2 | `SentimentTrend.jsx` | Recharts LineChart |
| 2 | `TopicDistribution.jsx` | Recharts BarChart |
| 3 | `NarrativeShift.jsx` | Recharts AreaChart |
| 3 | `MisinfoAlerts.jsx` | Review queue list |
| 4 | `LatestArticles.jsx` | Scrollable list with filters |
| 4 | `SourceSentiment.jsx` | Horizontal BarChart |
| 5 | `TopEntities.jsx` | 3-column ranked lists |
| 5 | `TrendingKeywords.jsx` | Ranked keyword list |

**Step 5: Layout**
- `Dashboard.jsx` — Tailwind 12-column grid composing all panels
- `Navbar.jsx` — app header

### Keep It Simple

- Each hook: `useState` + `useEffect` + fetch → return `{ data, loading, error }`
- Each panel: call hook, show `LoadingSpinner` while loading, render data
- Tailwind for layout — no custom CSS files
- No state management library — hooks + props are enough
- Auto-refresh only on `useMetrics` and `useSpikes` (30-min interval)

### Done When

- `npm start` loads the dashboard with no console errors
- All 9 panels show real data from the API
- Charts render with correct colors and labels
- Filters in LatestArticles work (topic, sentiment, source)

---

## Estimated Effort Per Module

| Module | Estimated Time | Files |
|---|---|---|
| 1. Database & Schema | 1-2 hours | 3 files + docker-compose |
| 2. Config & Settings | 30 min | 2 files + .env |
| 3. Ingestion Pipeline | 2-3 hours | 6 files |
| 4. NLP Pipeline | 2-3 hours | 6 files |
| 5. Aggregator | 1-2 hours | 3 files |
| 6. Scheduler | 1 hour | 2 files |
| 7. REST API | 2-3 hours | 9 files |
| 8. Frontend Dashboard | 4-6 hours | ~25 files |

**Total: ~15-22 hours of focused work**

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| NewsAPI quota exhaustion | Run NewsAPI every 2 hours only; RSS every 30 min |
| HuggingFace model download failures | Cache models locally after first download; fallback functions for each NLP step |
| Scraper blocked by site | Trafilatura fallback to title + description; 1s delay between requests |
| Empty dashboard on first load | Run pipeline immediately on app startup |
| Slow HuggingFace inference | Truncate to 512 tokens; use `bert-tiny` for misinfo (17MB, fast) |

---

## What We're Deliberately Skipping in v1

| Skipped | Why |
|---|---|
| Redis caching | Not needed until the UI is slow under load |
| TimescaleDB | PostgreSQL is fine for the expected data volume |
| D3 visualizations | Recharts handles all 9 panels |
| Alembic migrations | `create_all_tables()` is sufficient for dev |
| User authentication | Single-user dashboard, no auth needed |
| Pagination | `limit` parameter is enough for v1 |
| WebSocket live updates | Polling every 30 min matches the pipeline interval |
| Word cloud | Ranked keyword list is simpler and more informative |

 
 # #   M o d u l e   8 :   F r o n t e n d   D a s h b o a r d 
 
 # # #   I m p l e m e n t a t i o n   D e t a i l s 
 -   * * T e c h   S t a c k * * :   R e a c t   1 8 ,   V i t e ,   T a i l w i n d   C S S   3 . 4 ,   R e c h a r t s ,   L u c i d e - R e a c t . 
 -   * * D e s i g n   S y s t e m * * :   G l a s s m o r p h i s m   /   S o f t   U I   w i t h   a   M o n o c h r o m e   +   I n d i g o   p o i n t   a c c e n t   p a l e t t e . 
 -   * * D a r k   M o d e * * :   I n t e g r a t e d   u s i n g   T a i l w i n d   c l a s s   s t r a t e g y   a n d   u n i f i e d   l o c a l   s t a t e   t o g g l e   i n   H e a d e r . 
 -   * * P a n e l s   S t r u c t u r e d * * : 
     1 .   * * O v e r v i e w M e t r i c s * * :   T o p - l e v e l   d a s h b o a r d   s t a t s . 
     2 .   * * S e n t i m e n t T r e n d * * :   R e c h a r t s   L i n e C h a r t   f o r   a   7 / 1 4 / 3 0   d a y   r o l l i n g   t r e n d . 
     3 .   * * T o p i c D i s t r i b u t i o n * * :   H o r i z o n t a l   b a r   s e t u p . 
     4 .   * * N a r r a t i v e S h i f t * * :   A r e a   c h a r t   p a r s i n g   c o m p l e x   n e s t e d   s e r i e s . 
     5 .   * * M i s i n f o A l e r t s * * :   F i l t e r e d   p a n e l   s p e c i f i c a l l y   r e n d e r i n g   f l a g s   f l a g g e d   w i t h   s e v e r i t y   b a r s . 
     6 .   * * L a t e s t A r t i c l e s * * :   D e t a i l e d   t i m e l i n e   f e e d   u s i n g   \ d a t e - f n s \   r e l a t i v e   t i m e s . 
     7 .   * * S o u r c e S e n t i m e n t * * :   S o u r c e   q u a l i t y   a n d   b i a s   b r e a k d o w n . 
     8 .   * * T r e n d i n g K e y w o r d s * * :   L i s t e d   T F - I D F   f e a t u r e s   w i t h   t r e n d   i n d i c a t o r   i c o n s . 
     9 .   * * T o p E n t i t i e s * * :   C l e a n   l a y o u t   o f   o r g a n i z a t i o n s ,   l o c s ,   s u b j e c t s . 
 -   * * D a t a   C o n n e c t i v i t y * * :   C e n t r a l   \ u s e A p i D a t a \   h o o k   w r a p p i n g   A x i o s   p o l l i n g   t h e   b a c k e n d   A P I .  
 