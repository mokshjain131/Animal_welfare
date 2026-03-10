# Module Specifications

**News Sentiment Tracker** — Complete function-level specifications for every module.

---

## How to Read This Document

Each module section covers:
- Purpose and responsibility
- Files to create
- Every function with its signature, inputs, outputs, and logic
- How to verify the module works before moving on
- What can go wrong and how to handle it

> Build modules in order. Do not start a module until the previous one works.  
> Test each module in isolation before connecting it to the next.

---

## Module 1 — Database & Schema

**Purpose:**  
Define the entire PostgreSQL schema and manage all database connections.  
Every other module reads from or writes to tables defined here.  
This is the foundation — build it first.

**Files:**
```
backend/db/database.py
backend/db/models.py
backend/db/migrations/init.sql
```

---

### File: `backend/db/database.py`

This file creates the database connection and provides a session factory
that every other module imports to talk to PostgreSQL.

#### `get_engine()`

```python
def get_engine() -> Engine
```

**What it does:**  
Creates and returns a SQLAlchemy engine connected to PostgreSQL.
Reads the database URL from settings (`DATABASE_URL` environment variable).

**Inputs:** None. Reads `DATABASE_URL` from `config/settings.py`.  
**Outputs:** A SQLAlchemy `Engine` object.

**Logic:**
1. Import `create_engine` from sqlalchemy
2. Import `settings` from `config/settings.py`
3. Call `create_engine(settings.DATABASE_URL)`
4. Return the engine

**Error handling:**  
If `DATABASE_URL` is malformed or PostgreSQL is not running, SQLAlchemy will raise an `OperationalError` when the engine is first used. Let this fail loudly — it means the database is not set up correctly.

---

#### `get_session_factory()`

```python
def get_session_factory() -> sessionmaker
```

**What it does:**  
Creates and returns a session factory bound to the engine.
A session is how you run queries. The factory creates new sessions on demand.

**Logic:**
1. Call `get_engine()` to get the engine
2. Call `sessionmaker(bind=engine, autocommit=False, autoflush=False)`
3. Return the sessionmaker

---

#### `get_db()`

```python
def get_db() -> Generator
```

**What it does:**  
FastAPI dependency that yields a database session and closes it after use.
Used as dependency injection in all API route functions.

**Logic:**
1. Create a new session using the session factory
2. Yield the session (FastAPI uses it during the request)
3. In a `finally` block, close the session after the request is done

---

#### `create_all_tables()`

```python
def create_all_tables() -> None
```

**What it does:**  
Creates all database tables defined in `models.py` if they do not exist.
Called once at application startup.

**Logic:**
1. Import `Base` from `models.py`
2. Call `Base.metadata.create_all(bind=get_engine())`

---

### File: `backend/db/models.py`

Defines all SQLAlchemy table models. Each class is one table.

#### `Article` — table: `articles`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `url` | String(2048) | Unique, not null — used for deduplication |
| `title` | Text | Not null |
| `full_text` | Text | Nullable — may be empty if scraping failed |
| `source_name` | String(255) | Not null |
| `source_type` | String(50) | Not null — `"rss"`, `"newsapi"`, or `"trafilatura"` |
| `published_at` | DateTime | Not null |
| `created_at` | DateTime | Default: `now()` — when ingested |
| `is_processed` | Boolean | Default: `False` — `True` after NLP has run |

`is_processed` lets the NLP pipeline know which articles still need processing.

---

#### `SentimentScore` — table: `sentiment_scores`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `article_id` | Integer | Foreign key → `articles.id`, not null |
| `label` | String(20) | Not null — `"positive"`, `"negative"`, `"neutral"` |
| `score` | Float | Not null — confidence score between 0 and 1 |
| `created_at` | DateTime | Default: `now()` |

One row per article.

---

#### `TopicClassification` — table: `topics`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `article_id` | Integer | Foreign key → `articles.id`, not null |
| `topic` | String(100) | Not null — e.g. `"factory_farming"` |
| `confidence` | Float | Not null — classification confidence score |
| `created_at` | DateTime | Default: `now()` |

---

#### `Entity` — table: `entities`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `article_id` | Integer | Foreign key → `articles.id`, not null |
| `entity_text` | String(500) | Not null — e.g. `"WWF"` |
| `entity_type` | String(50) | Not null — `"ORG"`, `"GPE"`, `"ANIMAL"` |
| `created_at` | DateTime | Default: `now()` |

Multiple rows per article.

---

#### `FlaggedArticle` — table: `flagged_articles`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `article_id` | Integer | Foreign key → `articles.id`, not null, unique |
| `suspicion_score` | Float | Not null — misinfo confidence between 0 and 1 |
| `flag_reason` | String(500) | Nullable — short explanation |
| `is_reviewed` | Boolean | Default: `False` — analyst has reviewed it |
| `is_confirmed` | Boolean | Nullable — analyst confirmed or dismissed |
| `created_at` | DateTime | Default: `now()` |
| `reviewed_at` | DateTime | Nullable |

`is_reviewed` and `is_confirmed` support the analyst review workflow.

---

#### `TrendingKeyword` — table: `trending_keywords`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `phrase` | String(500) | Not null |
| `score` | Float | Not null — TF-IDF spike score |
| `article_count` | Integer | Not null — articles containing this phrase |
| `trend_direction` | String(10) | Not null — `"up"`, `"down"`, `"new"` |
| `topic` | String(100) | Nullable — topic category if identifiable |
| `computed_at` | DateTime | Default: `now()` |

This table is overwritten every 30 minutes by the aggregator.

---

#### `DailySummary` — table: `daily_summaries`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `date` | Date | Not null |
| `topic` | String(100) | Not null |
| `article_count` | Integer | Not null |
| `avg_sentiment` | Float | Not null |
| `positive_count` | Integer | Not null |
| `negative_count` | Integer | Not null |
| `neutral_count` | Integer | Not null |
| `created_at` | DateTime | Default: `now()` |

Unique constraint on `(date, topic)` — one row per topic per day.  
The dashboard reads from this table instead of running expensive real-time aggregations.

---

#### `SpikeEvent` — table: `spike_events`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `topic` | String(100) | Not null |
| `spike_date` | Date | Not null |
| `article_count` | Integer | Not null — count on the spike day |
| `weekly_avg` | Float | Not null — 7-day rolling average at time of spike |
| `multiplier` | Float | Not null — `article_count / weekly_avg` e.g. `2.1` |
| `is_active` | Boolean | Default: `True` — `False` when spike subsides |
| `detected_at` | DateTime | Default: `now()` |

---

#### `Keyphrase` — table: `keyphrases`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `article_id` | Integer | Foreign key → `articles.id`, not null |
| `phrase` | String(500) | Not null |
| `relevance_score` | Float | Not null — KeyBERT relevance score |
| `created_at` | DateTime | Default: `now()` |

Used as input to the TF-IDF aggregator.

---

### File: `backend/db/migrations/init.sql`

Raw SQL version of the schema. Used by Docker to initialize the database on first run. Should mirror `models.py` exactly.

Contains:
- `CREATE TABLE IF NOT EXISTS` statements for all 8 tables
- `CREATE INDEX` statements on commonly queried columns:
  - `articles.url` (unique index for deduplication lookups)
  - `articles.published_at` (time-range queries)
  - `articles.is_processed` (NLP pipeline queries)
  - `sentiment_scores.article_id`
  - `topics.topic`
  - `daily_summaries.date + daily_summaries.topic`
  - `spike_events.is_active`

---

### Verification — Module 1

1. Start PostgreSQL via `docker-compose up`
2. Run `create_all_tables()` in a Python shell
3. Connect to PostgreSQL and run `\dt` to list tables
4. Confirm all 8 tables exist with correct columns
5. Insert one test row into `articles` manually — confirm it saves and retrieves


---

## Module 2 — Configuration & Settings

**Purpose:**  
Single source of truth for all configuration values.  
API keys, database URLs, thresholds, keyword lists.  
Every other module imports from here. Nothing is hardcoded anywhere else.

**Files:**
```
backend/config/settings.py
backend/config/keywords.py
```

---

### File: `backend/config/settings.py`

#### `Settings` class *(inherits from `pydantic_settings.BaseSettings`)*

**What it does:**  
Reads environment variables from `.env` and validates them.
If a required variable is missing, the app fails at startup with a clear error.

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | `str` | — | e.g. `postgresql://admin:password@localhost:5432/sentiment_tracker` |
| `NEWSAPI_KEY` | `str` | — | Your NewsAPI.org API key |
| `RSS_FEEDS` | `list[str]` | BBC, Reuters, AP, Guardian, advocacy feeds | List of RSS feed URLs to monitor |
| `MISINFO_THRESHOLD` | `float` | `0.65` | Suspicion score above which an article is flagged |
| `FALLBACK_TEXT_LENGTH` | `int` | `150` | If scraped text is shorter, use title + description |
| `SPIKE_MULTIPLIER` | `float` | `2.0` | Topic must exceed this multiple of weekly average to trigger spike |
| `KEYBERT_TOP_N` | `int` | `5` | Number of keyphrases to extract per article |
| `TRENDING_KEYWORDS_TOP_N` | `int` | `10` | Number of trending phrases to show on dashboard |
| `PIPELINE_INTERVAL_MINUTES` | `int` | `30` | How often the ingestion + NLP pipeline runs |
| `APP_ENV` | `str` | `"development"` | Environment name |
| `LOG_LEVEL` | `str` | `"INFO"` | Logging verbosity |

```python
class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
```

At the bottom of `settings.py`:
```python
settings = Settings()
```

Every other module imports like this:
```python
from config.settings import settings
# Then uses: settings.NEWSAPI_KEY, settings.MISINFO_THRESHOLD, etc.
```

---

### File: `backend/config/keywords.py`

#### `TOPIC_KEYWORDS`

```python
TOPIC_KEYWORDS = {
  "factory_farming": [
    "factory farm", "factory farming", "industrial farming",
    "battery cage", "caged hens", "gestation crate", "feedlot",
    "slaughterhouse", "pig farming", "chicken farming", "broiler",
    "intensive farming", "confined animal feeding"
  ],
  "animal_testing": [
    "animal testing", "animal experimentation", "vivisection",
    "lab animals", "laboratory animals", "animal research",
    "cosmetics testing", "drug testing on animals", "animal trials"
  ],
  "wildlife": [
    "wildlife", "poaching", "ivory trade", "wildlife trafficking",
    "habitat destruction", "endangered species", "biodiversity",
    "illegal wildlife trade", "wildlife conservation", "trophy hunting",
    "deforestation", "animal extinction", "rhino horn", "elephant tusk"
  ],
  "pet_welfare": [
    "animal cruelty", "pet abuse", "dog fighting", "cockfighting",
    "puppy mill", "animal neglect", "companion animal", "pet welfare",
    "stray animals", "animal hoarding", "dogfighting"
  ],
  "animal_policy": [
    "animal welfare law", "animal rights bill", "animal protection act",
    "animal welfare policy", "animal legislation", "animal ban",
    "animal welfare regulation", "animal rights legislation"
  ],
  "veganism": [
    "vegan", "veganism", "plant-based", "plant based",
    "meat industry", "dairy industry", "animal agriculture",
    "meatless", "animal-free", "cruelty-free food"
  ]
}
```

---

#### `get_all_keywords()`

```python
def get_all_keywords() -> list[str]
```

**What it does:** Returns a flat list of all keywords across all topics.  
Used by the Relevance Gate for a quick any-match check.

**Logic:** Flatten `TOPIC_KEYWORDS.values()` into a single list and return it.

---

#### `get_topic_labels()`

```python
def get_topic_labels() -> list[str]
```

**What it does:** Returns a list of topic category names.  
Used as candidate labels for zero-shot topic classification.

**Logic:** Return `list(TOPIC_KEYWORDS.keys())`

---

#### `detect_topic_from_keywords(text: str)`

```python
def detect_topic_from_keywords(text: str) -> str | None
```

**What it does:**  
Simple fallback topic detection by keyword matching.  
Used if HuggingFace topic classifier is unavailable or too slow.  
Returns the topic with the most keyword matches, or `None` if no matches.

**Inputs:** `text` — the article `full_text` string  
**Outputs:** Topic string e.g. `"factory_farming"` or `None`

**Logic:**
1. Lowercase the input text
2. For each topic in `TOPIC_KEYWORDS`, count how many of its keywords appear in text
3. Return the topic with the highest count if `count > 0`, else return `None`

---

### Verification — Module 2

1. Create a `.env` file with all required variables
2. Import settings: `from config.settings import settings`
3. Print `settings.NEWSAPI_KEY` — confirm it reads correctly from `.env`
4. Call `get_all_keywords()` — confirm it returns a flat list
5. Call `detect_topic_from_keywords("factory farming investigation")` — should return `"factory_farming"`
6. Delete `NEWSAPI_KEY` from `.env` and reimport — should raise a `ValidationError` immediately

Logic:
  1. Lowercase the input text
  2. For each topic in TOPIC_KEYWORDS, count how many of its keywords appear in text
  3. Return the topic with the highest count if count > 0, else return None

--------------------------------------------------------------------------------
HOW TO VERIFY MODULE 2 WORKS
--------------------------------------------------------------------------------

1. Create a .env file with all required variables
2. Import settings in a Python shell: from config.settings import settings
3. Print settings.NEWSAPI_KEY — confirm it reads correctly from .env
4. Call get_all_keywords() — confirm it returns a flat list
5. Call detect_topic_from_keywords("factory farming investigation") — should return "factory_farming"
6. Delete NEWSAPI_KEY from .env and reimport — should raise a ValidationError immediately


---

## Module 3 — Ingestion Pipeline

**Purpose:**  
Fetch raw articles from RSS feeds and NewsAPI, extract full text, normalize all sources into one schema, remove duplicates, and filter for animal welfare relevance.  
Output: clean, relevant, unseen articles ready for NLP.

**Files:**
```
backend/ingestion/rss_fetcher.py
backend/ingestion/newsapi_fetcher.py
backend/ingestion/scraper.py
backend/ingestion/normalizer.py
backend/ingestion/deduplicator.py
backend/ingestion/relevance_gate.py
```

**Standard article schema** produced by all functions in this module:
```python
{
    "title":        str,
    "full_text":    str,
    "source_name":  str,
    "url":          str,
    "published_at": datetime,
    "source_type":  str   # "rss", "newsapi"
}
```

---

### File: `backend/ingestion/rss_fetcher.py`

#### `fetch_rss_feed(feed_url: str)`

```python
def fetch_rss_feed(feed_url: str) -> list[dict]
```

**What it does:**  
Fetches and parses a single RSS feed URL. Returns a list of raw article dicts.

**Inputs:** `feed_url` — e.g. `"https://feeds.bbci.co.uk/news/rss.xml"`  
**Outputs:** List of raw article dicts — `title`, `url`, `description`, `source_name`, `published_at`

**Logic:**
1. Call `feedparser.parse(feed_url)`
2. If `feed.boingodtype` is set, the feed failed — log and return empty list
3. For each entry in `feed.entries`: extract title, url, description, published_at, source_name
4. Return results list

**Error handling:** Wrap in `try/except`. Log and return `[]` on any exception. Never let one bad feed crash the entire ingestion run.

---

#### `fetch_all_rss_feeds()`

```python
def fetch_all_rss_feeds() -> list[dict]
```

**What it does:** Fetches all RSS feeds defined in `settings.RSS_FEEDS`. Returns combined list.

**Logic:**
1. For each `feed_url` in `settings.RSS_FEEDS`: call `fetch_rss_feed(feed_url)`
2. Extend combined results
3. Log total article count and return

---

### File: `backend/ingestion/newsapi_fetcher.py`

#### `fetch_newsapi_articles(query: str, page_size: int = 20)`

```python
def fetch_newsapi_articles(query: str, page_size: int = 20) -> list[dict]
```

**What it does:** Calls NewsAPI with a keyword query and returns matching articles.

**Logic:**
1. Initialize `NewsApiClient` with `settings.NEWSAPI_KEY`
2. Call `client.get_everything(q=query, language="en", sort_by="publishedAt", page_size=page_size)`
3. If status is not `"ok"`, log error and return `[]`
4. Extract and return article dicts

**Error handling:** Catch `NewsAPIException`. If key invalid, log: `"NewsAPI key invalid or exhausted"`

---

#### `fetch_all_newsapi_articles()`

```python
def fetch_all_newsapi_articles() -> list[dict]
```

**What it does:** Runs multiple NewsAPI queries across all topic keyword groups.

**Logic:**
1. For each topic, build a query from its first 3 keywords joined by `OR`  
   e.g. `"factory farm OR battery cage OR gestation crate"`
2. Call `fetch_newsapi_articles(query)` for each topic
3. Combine and return results

> **API quota note:** 100 requests/day on free tier. With 6 topics × 48 runs/day = 288 requests.  
> **Solution:** Run NewsAPI fetcher every 2 hours, RSS every 30 minutes. Add separate scheduler intervals.

---

### File: `backend/ingestion/scraper.py`

#### `scrape_full_text(url: str)`

```python
def scrape_full_text(url: str) -> str | None
```

**What it does:** Attempts to extract full article text from a URL using trafilatura.

**Logic:**
1. Call `trafilatura.fetch_url(url)` to download the page
2. Call `trafilatura.extract(downloaded)` to extract article text
3. If text is under `settings.FALLBACK_TEXT_LENGTH`, return `None`
4. Return the extracted text

**Error handling:** Wrap in `try/except`. Log URL + exception. Always return `None` on any exception.

---

#### `enrich_with_full_text(articles: list[dict])`

```python
def enrich_with_full_text(articles: list[dict]) -> list[dict]
```

**What it does:** Adds `full_text` to each article; falls back to `title + description` if scraping fails.

**Logic:**
1. For each article: call `scrape_full_text(article["url"])`
2. If result is not `None`: `article["full_text"] = result`
3. If `None`: `article["full_text"] = article["title"] + ". " + article.get("description", "")`
4. Add `time.sleep(1)` between requests to avoid rate limiting
5. Return the enriched list

> With 50 articles per run at 1s delay, scraping takes ~50 seconds — acceptable for a 30-minute interval pipeline.

---

### File: `backend/ingestion/normalizer.py`

#### `normalize_article(raw: dict, source_type: str)`

```python
def normalize_article(raw: dict, source_type: str) -> dict
```

**What it does:** Converts a raw article dict from any source into the standard article schema.

**Logic:**
1. Extract and clean title: strip whitespace, truncate to 1000 chars
2. Extract `full_text` from `raw["full_text"]` if present, else empty string
3. Clean `source_name`
4. Validate `url` starts with `http`
5. Ensure `published_at` is a `datetime` object — if parsing fails, use `datetime.now()`
6. Set `source_type` to the passed parameter
7. Return normalized dict

---

#### `normalize_all(rss_articles: list[dict], newsapi_articles: list[dict])`

```python
def normalize_all(rss_articles: list[dict], newsapi_articles: list[dict]) -> list[dict]
```

**What it does:** Normalizes articles from all sources into one unified list.

**Logic:**
1. Normalize each RSS article with `source_type="rss"`
2. Normalize each NewsAPI article with `source_type="newsapi"`
3. Combine into one list and return

---

### File: `backend/ingestion/deduplicator.py`

#### `get_existing_urls(db: Session)`

```python
def get_existing_urls(db: Session) -> set[str]
```

**What it does:** Fetches all article URLs from the database as a set for O(1) lookup.

---

#### `deduplicate(articles: list[dict], db: Session)`

```python
def deduplicate(articles: list[dict], db: Session) -> list[dict]
```

**What it does:** Removes articles whose URLs already exist in the database.  
Also removes duplicates within the current batch.

**Logic:**
1. Call `get_existing_urls(db)`
2. For each article: skip if URL is in existing URLs or already seen in this batch
3. Log how many dropped vs kept
4. Return results

---

### File: `backend/ingestion/relevance_gate.py`

#### `is_relevant(article: dict)`

```python
def is_relevant(article: dict) -> bool
```

**What it does:** Returns `True` if the article contains any animal welfare keywords.

**Logic:**
1. Combine `title + full_text` into one lowercase string
2. For each keyword in `get_all_keywords()`: return `True` immediately on first match
3. Return `False` if no match

---

#### `filter_relevant(articles: list[dict])`

```python
def filter_relevant(articles: list[dict]) -> tuple[list[dict], list[dict]]
```

**What it does:** Splits articles into relevant and irrelevant groups.

**Returns:** `(relevant_articles, rejected_articles)`

---

### Verification — Module 3

1. Run `fetch_all_rss_feeds()` — should return a list of raw article dicts
2. Run `fetch_all_newsapi_articles()` — should return articles with animal welfare terms
3. Run `enrich_with_full_text()` on a few articles — check `full_text` field is populated
4. Run `normalize_all()` — all articles should have the same keys
5. Run `deduplicate()` with an empty database — all articles should pass through
6. Run `deduplicate()` again immediately — all should be dropped (already saved)
7. Run `filter_relevant()` on a mixed list — confirm irrelevant articles are removed
8. Check the `articles` table in PostgreSQL — rows should be present


---

## Module 4 — NLP Pipeline

**Purpose:**  
Take a cleaned article and enrich it with all NLP outputs.
Sentiment score, topic classification, named entities, keyphrases, and misinformation suspicion score.
This module never fetches data — it only processes what ingestion provides.

**Files:**
```
backend/nlp/pipeline.py
backend/nlp/spacy_processor.py
backend/nlp/sentiment.py
backend/nlp/topic_classifier.py
backend/nlp/misinfo_detector.py
backend/nlp/keybert_extractor.py
```

---

### File: `backend/nlp/spacy_processor.py`

#### `load_spacy_model()`

```python
def load_spacy_model() -> Language
```

**What it does:** Loads the spaCy English model once and returns it.  
Called at module import time and cached — do not reload on every article.

**Logic:** Call `spacy.load("en_core_web_sm")` and return the model.

---

#### `extract_entities(text: str, nlp: Language)`

```python
def extract_entities(text: str, nlp: Language) -> list[dict]
```

**What it does:** Runs spaCy NER on the article text. Returns organisations, locations, and animal-related terms.

**Outputs:** List of entity dicts — `entity_text: str`, `entity_type: str` (`"ORG"`, `"GPE"`, `"ANIMAL"`)

**Logic:**
1. Run `nlp(text)` to get the spaCy `Doc` object
2. For each entity in `doc.ents`: include if `label_` is `"ORG"`, `"GPE"`, or `"LOC"`
3. Detect animals by checking `entity.text.lower()` against a predefined animal terms list (pig, chicken, cow, elephant, dolphin, whale, etc.)
4. Deduplicate entities by `(text, type)` pair
5. Return list of entity dicts

---

#### `clean_text(text: str, nlp: Language)`

```python
def clean_text(text: str, nlp: Language) -> str
```

**What it does:** Cleans article text for downstream NLP models.

**Logic:**
1. Run `nlp(text)`
2. Remove tokens that are pure punctuation or whitespace
3. Rejoin sentences and strip excessive whitespace
4. Return cleaned string

---

#### `process_article(text: str)`

```python
def process_article(text: str) -> dict
```

**What it does:** Main function — runs all spaCy processing on one article.

**Returns:** `{ "cleaned_text": str, "entities": list[dict] }`

---

### File: `backend/nlp/sentiment.py`

#### `load_sentiment_model()`

```python
def load_sentiment_model() -> pipeline
```

**What it does:** Loads HuggingFace sentiment model once and caches it.  
Model: `cardiffnlp/twitter-roberta-base-sentiment-latest`

```python
pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    truncation=True,
    max_length=512
)
```

> `truncation=True` silently truncates long articles to 512 tokens. The first 512 tokens usually contain the article's main sentiment signal.

---

#### `analyze_sentiment(text: str)`

```python
def analyze_sentiment(text: str) -> dict
```

**Returns:** `{ "label": str, "score": float }` — label is lowercase (`"positive"`, `"negative"`, `"neutral"`)

**Error handling:** On any exception, return `{"label": "neutral", "score": 0.0}` and log. Never let one article crash the pipeline.

---

### File: `backend/nlp/topic_classifier.py`

#### `load_topic_model()`

```python
def load_topic_model() -> pipeline
```

Model: `facebook/bart-large-mnli` (zero-shot classification)

---

#### `classify_topic(text: str)`

```python
def classify_topic(text: str) -> dict
```

**What it does:** Classifies article into one of the defined animal welfare topic categories.

**Returns:** `{ "topic": str, "confidence": float }`

**Logic:**
1. Call `model(text[:500], candidate_labels=get_topic_labels())`
2. Return top label and score

**Error handling:** Fall back to `detect_topic_from_keywords(text)` from Module 2 if model fails. Return `{"topic": fallback_topic or "unknown", "confidence": 0.0}`

---

### File: `backend/nlp/misinfo_detector.py`

#### `load_misinfo_model()`

```python
def load_misinfo_model() -> pipeline
```

Model: `mrm8488/bert-tiny-finetuned-fake-news-detection`

---

#### `score_misinfo(text: str)`

```python
def score_misinfo(text: str) -> dict
```

**Returns:**
```python
{
    "suspicion_score": float,   # 0–1
    "should_flag": bool,        # True if score >= settings.MISINFO_THRESHOLD
    "flag_reason": str
}
```

**Logic:**
1. Run model — returns `FAKE` or `REAL` label with confidence
2. If `FAKE`: `suspicion_score = confidence`
3. If `REAL`: `suspicion_score = 1 - confidence`
4. `should_flag = suspicion_score >= settings.MISINFO_THRESHOLD`
5. `flag_reason = "Flagged for review — model detected potentially misleading content"`

> **Important framing:** Never describe this as "confirmed misinformation" anywhere. It is a suspicion score. Always say "flagged for review".

---

### File: `backend/nlp/keybert_extractor.py`

#### `load_keybert_model()`

```python
def load_keybert_model() -> KeyBERT
```

Downloads `sentence-transformers` model on first run (~90MB). Cache after first load.

---

#### `extract_keyphrases(text: str)`

```python
def extract_keyphrases(text: str) -> list[dict]
```

**Returns:** List of `{ "phrase": str, "relevance_score": float }`

**Logic:**
```python
model.extract_keywords(
    text,
    keyphrase_ngram_range=(1, 3),
    stop_words="english",
    top_n=settings.KEYBERT_TOP_N
)
```

**Error handling:** If text is under 50 chars or any exception occurs, return `[]`.

---

### File: `backend/nlp/pipeline.py`

This is the orchestrator. Calls all NLP functions in sequence on a single article and saves all results to the database.

#### `process_article(article: dict, db: Session)`

```python
def process_article(article: dict, db: Session) -> None
```

**What it does:** Runs the complete NLP pipeline on one article. Saves all results. Marks article as processed.

**Logic:**
1. **spaCy:** `spacy_processor.process_article(article["full_text"])` → save entities to `entities` table
2. **Sentiment:** `sentiment.analyze_sentiment(cleaned_text)` → save to `sentiment_scores`
3. **Topic:** `topic_classifier.classify_topic(cleaned_text)` → save to `topics`
4. **Misinfo:** `misinfo_detector.score_misinfo(cleaned_text)` → save to `flagged_articles` if `should_flag`
5. **KeyBERT:** `keybert_extractor.extract_keyphrases(cleaned_text)` → save to `keyphrases`
6. **Mark processed:** Update `articles.is_processed = True`
7. **Commit** the database session

**Error handling:** Wrap in `try/except`. Log error with article URL. Still mark as processed to avoid endless retries. Partial results are better than no results.

---

#### `process_unprocessed_articles(db: Session)`

```python
def process_unprocessed_articles(db: Session) -> int
```

**What it does:** Fetches all `is_processed=False` articles and runs the NLP pipeline on each.

**Returns:** Integer count of articles processed.

**Logic:**
1. Query `articles` where `is_processed=False`
2. For each article: call `process_article(article, db)`
3. Log progress every 10 articles
4. Return total count

---

### Verification — Module 4

1. Insert a test article into the database manually
2. Call `process_unprocessed_articles()` with a db session
3. Check `sentiment_scores` — should have one row for the test article
4. Check `topics` — should have one row with a topic label
5. Check `entities` — should have rows for any orgs/locations in the article
6. Check `keyphrases` — should have 3–5 keyphrase rows
7. Check `articles.is_processed = True` for the test article
8. Test with a clearly positive and a clearly negative article — confirm sentiment labels are correct
  1. Query articles table for all rows where is_processed=False
  2. For each article, call process_article(article, db)
  3. Log progress every 10 articles
  4. Return total count processed

--------------------------------------------------------------------------------
HOW TO VERIFY MODULE 4 WORKS
--------------------------------------------------------------------------------

1. Insert a test article into the database manually
2. Call process_unprocessed_articles() with a db session
3. Check sentiment_scores — should have one row for the test article
4. Check topics — should have one row with a topic label
5. Check entities — should have rows for any orgs/locations in the article
6. Check keyphrases — should have 3-5 keyphrase rows
7. Check articles.is_processed = True for the test article
8. Test with a clearly positive article and a clearly negative article
   and confirm the sentiment labels are correct


---

## Module 5 — Aggregator

**Purpose:** Run scheduled computations on the full article corpus. Produce pre-computed summary tables so the dashboard never runs slow real-time aggregation queries. Three jobs: daily summaries, trending keywords, spike detection.

**Files:**
- `backend/aggregator/daily_summary.py`
- `backend/aggregator/tfidf_keywords.py`
- `backend/aggregator/spike_detector.py`

---

### File: `backend/aggregator/daily_summary.py`

#### `compute_daily_summaries()`

```python
def compute_daily_summaries(db: Session) -> None
```

Computes per-topic sentiment aggregates for today and writes them to the `daily_summaries` table. Overwrites existing rows for today.

| Parameter | Type | Description |
|---|---|---|
| `db` | `Session` | SQLAlchemy database session |

**Logic:**
1. Get today's date
2. For each topic in `get_topic_labels()`:
   - Query articles joined with `sentiment_scores` and `topics` where `topics.topic = current_topic` and `articles.published_at >= today midnight`
   - Count total, positive, negative, and neutral articles
   - Compute average sentiment score
   - Upsert one row in `daily_summaries` with `(date=today, topic=current_topic, counts, avg_sentiment)`
3. Commit

#### `compute_historical_summaries()`

```python
def compute_historical_summaries(db: Session, days_back: int = 30) -> None
```

Same as `compute_daily_summaries` but for the past N days. Run this once when first setting up the system to backfill history.

**Logic:** For each date in the past `days_back` days, call the same aggregation logic as `compute_daily_summaries` scoped to that specific date.

---

### File: `backend/aggregator/tfidf_keywords.py`

#### `compute_trending_keywords()`

```python
def compute_trending_keywords(db: Session) -> None
```

Computes which keyphrases are statistically spiking today compared to the past 7 days. Writes top results to the `trending_keywords` table.

| Parameter | Type | Description |
|---|---|---|
| `db` | `Session` | SQLAlchemy database session |

**Logic:**
1. Fetch all keyphrases from the last 24 hours → `today_counts`
2. Fetch all keyphrases from the last 7 days → `baseline_counts`
3. For each phrase in `today_counts`:
   - Compute `baseline_avg = baseline_counts.get(phrase, 0) / 7`
   - Compute `spike_score = today_count / max(baseline_avg, 1)`
   - Determine `trend_direction`: `"new"` if not in baseline, `"up"` if `spike_score > 1.5`, `"down"` if `< 0.5`, otherwise `"stable"`
4. Sort by `spike_score` descending
5. Take top `settings.TRENDING_KEYWORDS_TOP_N` phrases
6. Delete all existing rows in `trending_keywords`, insert new top phrases
7. Commit

> **Note:** You can use scikit-learn's `TfidfVectorizer` for a more rigorous approach. For a prototype, frequency comparison is sufficient and easier to explain to reviewers.

---

### File: `backend/aggregator/spike_detector.py`

#### `compute_weekly_average()`

```python
def compute_weekly_average(topic: str, db: Session) -> float
```

Computes the average daily article count for a topic over the past 7 days.

| Parameter | Type | Description |
|---|---|---|
| `topic` | `str` | Topic string, e.g. `"factory_farming"` |
| `db` | `Session` | SQLAlchemy database session |

**Returns:** `float` — average articles per day for that topic over 7 days.

**Logic:**
1. Query `daily_summaries` for rows where `topic = topic` and `date` is within the last 7 days
2. Sum `article_count` values, divide by 7 (even if some days have 0 articles)

#### `detect_spikes()`

```python
def detect_spikes(db: Session) -> list[dict]
```

Checks each topic for a spike in today's article count. Creates `spike_events` records for new spikes and resolves events that have subsided.

| Parameter | Type | Description |
|---|---|---|
| `db` | `Session` | SQLAlchemy database session |

**Returns:** `list[dict]` — list of newly detected spikes.

**Logic:**
1. For each topic in `get_topic_labels()`:
   - Get today's article count from `daily_summaries`
   - Call `compute_weekly_average(topic, db)`
   - Compute `multiplier = today_count / max(weekly_avg, 1)`
   - If `multiplier >= settings.SPIKE_MULTIPLIER`: insert a new row into `spike_events` with `is_active=True` (skip if one already exists for today)
   - Otherwise: set `is_active=False` on any active spike for this topic
2. Commit and return list of newly detected spikes

#### `run_aggregator()`

```python
def run_aggregator(db: Session) -> None
```

Runs all three aggregator jobs in sequence. This is the function called by the scheduler.

**Logic:**
1. Call `compute_daily_summaries(db)`
2. Call `compute_trending_keywords(db)`
3. Call `detect_spikes(db)`
4. Log completion time

---

### Verification

1. Ensure the database has at least a few days of processed articles
2. Run `run_aggregator()` manually
3. Query `daily_summaries` — should have rows per topic per day
4. Query `trending_keywords` — should have top 10 phrases
5. Query `spike_events` — if any topic had a spike, should have an active row
6. Run the aggregator again immediately — `daily_summaries` should be overwritten with the same values (idempotent), not duplicated

---

## Module 6 — Scheduler

**Purpose:** Wire everything together into one automated pipeline. Ingestion + NLP + Aggregation runs on a schedule without manual intervention. This module is the glue between all backend modules.

**Files:**
- `backend/ingestion/scheduler.py`
- `backend/main.py`

---

### File: `backend/ingestion/scheduler.py`

#### `run_ingestion_pipeline()`

```python
def run_ingestion_pipeline() -> None
```

Executes the complete ingestion pipeline in sequence. This is the function the scheduler calls every 15–30 minutes.

**Logic:**

| Step | Action |
|---|---|
| 1 | Log pipeline start with timestamp |
| 2 | `articles_rss = fetch_all_rss_feeds()` |
| 3 | `articles_newsapi = fetch_all_newsapi_articles()` (only on "even" runs to conserve API quota) |
| 4 | `enriched = enrich_with_full_text(articles_rss + articles_newsapi)` |
| 5 | `normalized = normalize_all(rss_articles, newsapi_articles)` |
| 6 | `unique = deduplicate(normalized, db)` |
| 7 | `relevant, rejected = filter_relevant(unique)` |
| 8 | Insert each `relevant` article into `articles` with `is_processed=False` |
| 9 | `process_unprocessed_articles(db)` |
| 10 | `run_aggregator(db)` |
| 11 | Log totals: fetched, saved, processed, rejected |
| 12 | Close db session |

> **Error handling:** Wrap the entire function in `try/except`. Log errors with full traceback. A failed run must never bring down the app — the scheduler continues regardless.

#### `create_scheduler()`

```python
def create_scheduler() -> BackgroundScheduler
```

Creates and configures the APScheduler instance. Adds the pipeline job at the configured interval.

**Logic:**
1. Create a `BackgroundScheduler` instance
2. Add job:
   ```python
   scheduler.add_job(
       func=run_ingestion_pipeline,
       trigger=IntervalTrigger(minutes=settings.PIPELINE_INTERVAL_MINUTES),
       id="ingestion_pipeline",
       replace_existing=True
   )
   ```
3. Return scheduler (do not start here — start in `main.py`)

---

### File: `backend/main.py`

#### `create_app()`

```python
def create_app() -> FastAPI
```

Creates and configures the FastAPI application. Registers all routers, starts the scheduler, and sets up startup/shutdown events.

**CORS Middleware:**

| Setting | Value |
|---|---|
| Allow origins | `["http://localhost:3000"]` |
| Allow methods | `["GET"]` |
| Allow headers | `["*"]` |

**Routers:**

| Prefix | Router |
|---|---|
| `/overview` | `metrics_router` |
| `/sentiment` | `sentiment_router` |
| `/topics` | `topics_router` |
| `/narrative` | `narrative_router` |
| `/articles` | `articles_router` |
| `/trending` | `keywords_router` |
| `/entities` | `entities_router` |
| `/spikes` | `spikes_router` |
| `/sources` | `sources_router` |

**Startup event:**
```python
@app.on_event("startup")
async def startup():
    create_all_tables()
    scheduler = create_scheduler()
    scheduler.start()
    run_ingestion_pipeline()  # run immediately so dashboard has data
```

**Shutdown event:**
```python
@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
```

**Run command:**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Verification

1. Start the app: `uvicorn backend.main:app --reload`
2. Check logs — should see "Pipeline started" and "Pipeline completed" messages
3. Check the database — `articles` table should be populated after startup
4. Wait 30 minutes — check logs again for a second pipeline run
5. Visit `http://localhost:8000/docs` — FastAPI docs should show all 10 endpoints

---

## Module 7 — REST API

**Purpose:** Serve pre-computed data from PostgreSQL to the React frontend. 10 endpoints, each reading from summary tables — never raw aggregations. All endpoints return JSON.

**Files:**

| File | Endpoint |
|---|---|
| `backend/api/routes/metrics.py` | `GET /overview/metrics` |
| `backend/api/routes/sentiment.py` | `GET /sentiment/trend` |
| `backend/api/routes/topics.py` | `GET /topics/volume` |
| `backend/api/routes/narrative.py` | `GET /narrative/shifts` |
| `backend/api/routes/articles.py` | `GET /articles/recent`, `GET /articles/flagged` |
| `backend/api/routes/keywords.py` | `GET /trending/keywords` |
| `backend/api/routes/entities.py` | `GET /entities/top` |
| `backend/api/routes/spikes.py` | `GET /spikes/active` |
| `backend/api/routes/sources.py` | `GET /sources/sentiment` |

> All route files follow the same pattern: create an `APIRouter`, define route functions with `db: Session = Depends(get_db)`, query the database, and return a dict or list.

---

### `GET /overview/metrics`

Returns the four overview metric values for the dashboard stat cards.

```json
{
  "articles_today": 42,
  "avg_sentiment": 0.21,
  "avg_sentiment_label": "positive",
  "avg_sentiment_vs_yesterday": 0.05,
  "active_topics": 5,
  "misinfo_alerts": 3,
  "active_spike": {
    "topic": "factory_farming",
    "multiplier": 2.1,
    "detected_at": "2026-03-07T14:30:00"
  }
}
```

---

### `GET /sentiment/trend`

| Query Param | Type | Default | Description |
|---|---|---|---|
| `topic` | `str` | _(none)_ | Filter by topic |
| `days` | `int` | `7` | Number of days to return |

```json
{
  "data": [
    {"date": "2026-03-07", "avg_sentiment": 0.42, "article_count": 18, "topic": "factory_farming"}
  ]
}
```

---

### `GET /topics/volume`

| Query Param | Type | Default |
|---|---|---|
| `days` | `int` | `7` |

```json
{
  "data": [
    {"topic": "factory_farming", "article_count": 142},
    {"topic": "wildlife", "article_count": 89}
  ]
}
```

---

### `GET /narrative/shifts`

| Query Param | Type | Default |
|---|---|---|
| `days` | `int` | `14` |

```json
{
  "dates": ["2026-03-01", "2026-03-02"],
  "series": [
    {"topic": "factory_farming", "values": [4, 6, 18, 7, 3]}
  ]
}
```

---

### `GET /articles/recent`

| Query Param | Type | Default |
|---|---|---|
| `limit` | `int` | `20` |
| `topic` | `str` | _(optional)_ |
| `sentiment` | `str` | _(optional)_ — `"positive"`, `"negative"`, `"neutral"` |
| `source` | `str` | _(optional)_ |

```json
{
  "articles": [
    {
      "id": 1,
      "title": "...",
      "url": "...",
      "source_name": "Reuters",
      "published_at": "2026-03-07T10:00:00",
      "topic": "wildlife",
      "sentiment_label": "positive",
      "sentiment_score": 0.72,
      "is_flagged": false
    }
  ]
}
```

---

### `GET /articles/flagged`

| Query Param | Type | Default |
|---|---|---|
| `limit` | `int` | `20` |

Returns articles ordered by `suspicion_score` descending where `is_reviewed=False`.

```json
{
  "articles": [
    {
      "id": 1,
      "title": "...",
      "url": "...",
      "source_name": "Reuters",
      "suspicion_score": 0.91,
      "flag_reason": "...",
      "published_at": "2026-03-07T10:00:00"
    }
  ]
}
```

---

### `GET /trending/keywords`

```json
{
  "keywords": [
    {
      "phrase": "factory farm investigation",
      "score": 4.2,
      "article_count": 12,
      "trend_direction": "up",
      "topic": "factory_farming"
    }
  ]
}
```

---

### `GET /entities/top`

| Query Param | Type | Default |
|---|---|---|
| `days` | `int` | `7` |
| `limit` | `int` | `5` per type |

```json
{
  "organizations": [{"name": "WWF", "count": 24}, {"name": "PETA", "count": 18}],
  "locations": [{"name": "United Kingdom", "count": 31}],
  "animals": [{"name": "pigs", "count": 45}]
}
```

---

### `GET /spikes/active`

```json
{
  "spikes": [
    {
      "topic": "factory_farming",
      "multiplier": 2.1,
      "article_count": 18,
      "weekly_avg": 8.5,
      "detected_at": "2026-03-07T14:30:00"
    }
  ]
}
```

---

### `GET /sources/sentiment`

| Query Param | Type | Default |
|---|---|---|
| `limit` | `int` | `10` |
| `days` | `int` | `7` |

```json
{
  "sources": [
    {"source_name": "Reuters", "article_count": 45, "avg_sentiment": 0.12, "sentiment_label": "neutral"}
  ]
}
```

---

### Verification

1. Start the FastAPI app
2. Visit `http://localhost:8000/docs`
3. Test each endpoint using the interactive docs UI
4. Confirm every endpoint returns valid JSON with the expected shape
5. Test with query parameters — topic filter, date range, limit
6. Confirm all endpoints respond under 200ms (they read from pre-computed tables)

---

## Module 8 — Frontend Dashboard

**Purpose:** Consume the REST API and render the 9-panel dashboard. Each panel is independent with its own data-fetching hook. Build shared utilities first, then panels in row order.

**Files:**

| Category | Path |
|---|---|
| API client | `frontend/src/utils/api.js` |
| Constants | `frontend/src/utils/constants.js` |
| Formatters | `frontend/src/utils/formatters.js` |
| Shared components | `frontend/src/components/shared/*.jsx` |
| Hooks | `frontend/src/hooks/*.js` |
| Panel components | `frontend/src/components/panels/*.jsx` |
| Layout | `frontend/src/components/layout/Dashboard.jsx` |

---

### File: `frontend/src/utils/api.js`

Creates and exports an `axios` instance configured with the base API URL. All hooks import this instead of using axios directly.

```js
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 10000
})
// Add response interceptor that logs errors to console
```

**Exported functions:**

| Function | Endpoint |
|---|---|
| `fetchMetrics()` | `GET /overview/metrics` |
| `fetchSentimentTrend(topic, days)` | `GET /sentiment/trend` |
| `fetchTopicsVolume(days)` | `GET /topics/volume` |
| `fetchNarrativeShifts(days)` | `GET /narrative/shifts` |
| `fetchRecentArticles(limit, topic, sentiment, source)` | `GET /articles/recent` |
| `fetchFlaggedArticles(limit)` | `GET /articles/flagged` |
| `fetchTrendingKeywords()` | `GET /trending/keywords` |
| `fetchTopEntities(days, limit)` | `GET /entities/top` |
| `fetchActiveSpikes()` | `GET /spikes/active` |
| `fetchSourceSentiment(limit, days)` | `GET /sources/sentiment` |

---

### File: `frontend/src/utils/constants.js`

**`TOPIC_COLORS`**

| Topic | Color |
|---|---|
| `factory_farming` | `#ef4444` |
| `wildlife` | `#22c55e` |
| `animal_testing` | `#3b82f6` |
| `pet_welfare` | `#f59e0b` |
| `animal_policy` | `#8b5cf6` |
| `veganism` | `#14b8a6` |

**`SENTIMENT_COLORS`**

| Sentiment | Color |
|---|---|
| `positive` | `#22c55e` |
| `negative` | `#ef4444` |
| `neutral` | `#94a3b8` |

**`REFRESH_INTERVAL`:** `30 * 60 * 1000` ms (30 minutes) — used by hooks for auto-refresh.

---

### File: `frontend/src/utils/formatters.js`

| Function | Description |
|---|---|
| `formatDate(dateString)` | ISO date → `"Mar 7"` or `"Mar 7, 2026"` using `date-fns format()` |
| `formatSentimentScore(score)` | `0.423` → `"+0.42"` with sign |
| `formatTopicLabel(topicKey)` | `"factory_farming"` → `"Factory Farming"` |
| `getSentimentColor(label)` | Returns hex from `SENTIMENT_COLORS` |
| `getTopicColor(topicKey)` | Returns hex from `TOPIC_COLORS` |
| `formatRelativeTime(dateString)` | Returns `"2 hours ago"` using `date-fns formatDistanceToNow()` |

---

### Shared Components

| Component | Props | Description |
|---|---|---|
| `SentimentBadge.jsx` | `label`, `score` | Colored badge: "Positive / Negative / Neutral" with score |
| `TopicBadge.jsx` | `topic` | Colored badge with human-readable topic label |
| `SpikeBanner.jsx` | `spike` | Red alert banner if spike is active; renders nothing if `null` |
| `MisinfoFlag.jsx` | `score` | Flag icon with suspicion score tooltip; hidden when score is 0 |
| `LoadingSpinner.jsx` | _(none)_ | Centered spinner shown while data loads |

---

### Hooks

Each hook follows the pattern: `useState` for data/loading/error → `useEffect` calls the relevant API function → optional `setInterval` for auto-refresh → returns `{ data, loading, error }`.

| Hook | API call | Returns | Auto-refresh |
|---|---|---|---|
| `useMetrics.js` | `fetchMetrics()` | `{ metrics, loading, error }` | Yes (30 min) |
| `useSentimentTrend.js` | `fetchSentimentTrend(topic, days)` | `{ trendData, loading, error }` | Re-fetches on filter change |
| `useTopics.js` | `fetchTopicsVolume()` | `{ topicsData, loading, error }` | — |
| `useNarrative.js` | `fetchNarrativeShifts()` | `{ narrativeData, loading, error }` | — |
| `useArticles.js` | `fetchRecentArticles()` + `fetchFlaggedArticles()` | `{ articles, flaggedArticles, loading, error }` | — |
| `useKeywords.js` | `fetchTrendingKeywords()` | `{ keywords, loading, error }` | — |
| `useEntities.js` | `fetchTopEntities()` | `{ entities, loading, error }` | — |
| `useSpikes.js` | `fetchActiveSpikes()` | `{ spikes, loading, error }` | Yes (30 min) |
| `useSources.js` | `fetchSourceSentiment()` | `{ sourcesData, loading, error }` | — |

---

### Panel Components

| Component | Hook(s) | Description |
|---|---|---|
| `OverviewMetrics.jsx` | `useMetrics`, `useSpikes` | `SpikeBanner` + 4 stat cards (Articles Today, Avg Sentiment, Active Topics, Misinfo Alerts) |
| `SentimentTrend.jsx` | `useSentimentTrend` | Recharts `LineChart` with topic filter dropdown and 7d/30d/all time range selector |
| `TopicDistribution.jsx` | `useTopics` | Recharts horizontal `BarChart` sorted by article count |
| `NarrativeShift.jsx` | `useNarrative` | Recharts `AreaChart` with one colored area per topic |
| `MisinfoAlerts.jsx` | `useArticles` (flagged) | List of flagged articles with suspicion score bar and flag reason |
| `LatestArticles.jsx` | `useArticles` | Scrollable list with filter bar (topic, sentiment, source) |
| `SourceSentiment.jsx` | `useSources` | Recharts horizontal `BarChart` colored by sentiment; click to filter `LatestArticles` |
| `TopEntities.jsx` | `useEntities` | Three columns (Organizations, Locations, Animals), top 5 each with count badge |
| `TrendingKeywords.jsx` | `useKeywords` | Ranked list of top 10 keyphrases with count and trend direction arrow |

---

### File: `frontend/src/components/layout/Dashboard.jsx`

Composes all panel components into a 5-row Tailwind CSS grid.

| Row | Left | Right |
|---|---|---|
| Row 1 | `<OverviewMetrics />` (full width, `col-span-12`) | — |
| Row 2 | `<SentimentTrend />` (`col-span-8`) | `<TopicDistribution />` (`col-span-4`) |
| Row 3 | `<NarrativeShift />` (`col-span-8`) | `<MisinfoAlerts />` (`col-span-4`) |
| Row 4 | `<LatestArticles />` (`col-span-9`) | `<SourceSentiment />` (`col-span-3`) |
| Row 5 | `<TopEntities />` (`col-span-6`) | `<TrendingKeywords />` (`col-span-6`) |

---

### Verification

1. Run `npm start` in the frontend directory
2. The dashboard should load without console errors
3. All 9 panels should show real data (no loading spinners)
4. The Spike Banner should appear or not based on `spike_events` in the database
5. Test each filter in `LatestArticles` — topic, sentiment, source
6. Confirm Recharts charts render with real data
7. Check the network tab — all API calls should return `200`

---

## Final Build Order Checklist

Complete each module's verification checks before moving to the next. This is the single most important discipline for a one-week build.

| # | Module | Description |
|---|---|---|
| 1 | Database & Schema | Start PostgreSQL, create tables |
| 2 | Configuration & Settings | `.env` set up, keywords defined |
| 3 | Ingestion Pipeline | Articles flowing into database |
| 4 | NLP Pipeline | Articles enriched with scores |
| 5 | Aggregator | Summary tables populated |
| 6 | Scheduler | Everything running automatically |
| 7 | REST API | All endpoints returning data at `/docs` |
| 8 | Frontend Dashboard | All 9 panels rendering real data |

---

*News Sentiment Tracker · Complete Module Specifications · May 2026*

