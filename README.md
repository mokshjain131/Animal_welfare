# Animal Welfare News Sentiment Tracker

A full-stack dashboard that ingests animal welfare news from RSS feeds and NewsAPI, enriches articles with NLP (sentiment, topic classification, entity recognition, misinformation detection), and visualises the results in a 9-panel React dashboard.

---

## Repository Structure

```
news-sentiment-tracker/
│
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
│
├── backend/
│   ├── main.py                        # FastAPI app entry point, APScheduler setup
│   ├── requirements.txt
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── metrics.py             # GET /overview/metrics
│   │       ├── sentiment.py           # GET /sentiment/trend
│   │       ├── topics.py              # GET /topics/volume
│   │       ├── narrative.py           # GET /narrative/shifts
│   │       ├── articles.py            # GET /articles/recent, /articles/flagged
│   │       ├── keywords.py            # GET /trending/keywords
│   │       ├── entities.py            # GET /entities/top
│   │       ├── spikes.py              # GET /spikes/active
│   │       └── sources.py             # GET /sources/sentiment
│   │
│   ├── ingestion/
│   │   ├── scheduler.py               # APScheduler job definitions
│   │   ├── rss_fetcher.py             # RSS feed parsing
│   │   ├── newsapi_fetcher.py         # NewsAPI calls
│   │   ├── scraper.py                 # Trafilatura full-text extraction
│   │   ├── normalizer.py              # Merges all sources into standard schema
│   │   ├── deduplicator.py            # URL-based duplicate check
│   │   └── relevance_gate.py          # Keyword filter before NLP
│   │
│   ├── nlp/
│   │   ├── pipeline.py                # Orchestrates all NLP steps in order
│   │   ├── spacy_processor.py         # NER, tokenization, segmentation
│   │   ├── sentiment.py               # HuggingFace sentiment analysis
│   │   ├── topic_classifier.py        # HuggingFace topic classification
│   │   ├── misinfo_detector.py        # HuggingFace misinformation scoring
│   │   └── keybert_extractor.py       # KeyBERT keyphrase extraction
│   │
│   ├── aggregator/
│   │   ├── daily_summary.py           # Writes pre-computed rows to daily_summaries
│   │   ├── tfidf_keywords.py          # TF-IDF trending keyword computation
│   │   └── spike_detector.py          # Rolling average spike logic
│   │
│   ├── db/
│   │   ├── database.py                # PostgreSQL connection, session management
│   │   ├── models.py                  # SQLAlchemy table definitions
│   │   └── migrations/
│   │       └── init.sql               # Initial schema creation script
│   │
│   ├── config/
│   │   ├── settings.py                # Loads env vars, API keys, config values
│   │   └── keywords.py                # Animal welfare keyword lists per topic
│   │
│   └── tests/
│       ├── test_ingestion.py
│       ├── test_nlp.py
│       └── test_aggregator.py
│
├── frontend/
│   ├── package.json
│   ├── .env.example                   # REACT_APP_API_URL=http://localhost:8000
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       ├── App.js
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Dashboard.jsx      # Main layout, row composition
│       │   │   └── Navbar.jsx
│       │   ├── panels/
│       │   │   ├── OverviewMetrics.jsx        # Row 1 — stat cards + spike banner
│       │   │   ├── SentimentTrend.jsx         # Row 2 — line chart
│       │   │   ├── TopicDistribution.jsx      # Row 2 — bar chart
│       │   │   ├── NarrativeShift.jsx         # Row 3 — stacked area chart
│       │   │   ├── MisinfoAlerts.jsx          # Row 3 — review queue
│       │   │   ├── LatestArticles.jsx         # Row 4 — scrollable feed
│       │   │   ├── SourceSentiment.jsx        # Row 4 — source comparison bars
│       │   │   ├── TopEntities.jsx            # Row 5 — NER ranked lists
│       │   │   └── TrendingKeywords.jsx       # Row 5 — keyword list
│       │   └── shared/
│       │       ├── SentimentBadge.jsx         # Reusable pos/neg/neutral tag
│       │       ├── TopicBadge.jsx             # Reusable topic category tag
│       │       ├── SpikeBanner.jsx            # Conditional spike alert banner
│       │       ├── MisinfoFlag.jsx            # Flag icon with score tooltip
│       │       └── LoadingSpinner.jsx
│       ├── hooks/
│       │   ├── useMetrics.js          # Fetches /overview/metrics
│       │   ├── useSentimentTrend.js   # Fetches /sentiment/trend
│       │   ├── useTopics.js           # Fetches /topics/volume
│       │   ├── useNarrative.js        # Fetches /narrative/shifts
│       │   ├── useArticles.js         # Fetches /articles/recent + /articles/flagged
│       │   ├── useKeywords.js         # Fetches /trending/keywords
│       │   ├── useEntities.js         # Fetches /entities/top
│       │   ├── useSpikes.js           # Fetches /spikes/active
│       │   └── useSources.js          # Fetches /sources/sentiment
│       └── utils/
│           ├── api.js                 # Base API client, base URL config
│           ├── formatters.js          # Date formatting, score rounding, etc.
│           └── constants.js           # Topic names, colour maps, thresholds
│
└── docs/
    ├── architecture.md
    ├── feature-list.md
    ├── data-flow.md
    ├── documentation.md
    ├── dashboard-layout.md
    ├── setup.md
    ├── thinking-process.md
    ├── module-specifications.md
    ├── module-requirements.md
    └── future-scope.md
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Backend** | Python · FastAPI | REST API + scheduler host |
| **NLP — entities** | spaCy `en_core_web_sm` | NER, tokenization, segmentation |
| **NLP — classification** | HuggingFace Transformers | Sentiment, topic, misinformation |
| **NLP — keyphrases** | KeyBERT | Semantic keyphrase extraction |
| **Ingestion** | RSS + NewsAPI + Trafilatura | Full-text extraction; `newspaper3k`/`newspaper4k` as alternatives |
| **Database** | PostgreSQL | TimescaleDB is a natural upgrade for time-series |
| **Scheduler** | APScheduler | Runs pipeline every 15–30 min; cron job is an alternative |
| **Frontend** | React + Recharts | D3 if highly custom visualisation is needed later |
| **Caching** | Redis *(future)* | Add if the UI feels sluggish under load |

### HuggingFace Models

| Task | Model |
|---|---|
| Sentiment analysis | `cardiffnlp/twitter-roberta-base-sentiment-latest` |
| Topic classification (zero-shot) | `facebook/bart-large-mnli` |
| Misinformation detection | `mrm8488/bert-tiny-finetuned-fake-news-detection` |

All models are free, open weights, and download automatically on first use. No API key required.

---

## Documentation

| File | Description |
|---|---|
| [docs/architecture.md](docs/architecture.md) | System architecture by layer |
| [docs/data-flow.md](docs/data-flow.md) | End-to-end pipeline flow |
| [docs/feature-list.md](docs/feature-list.md) | Full feature list with priorities |
| [docs/module-requirements.md](docs/module-requirements.md) | Per-module package requirements |
| [docs/module-specifications.md](docs/module-specifications.md) | Function-level specifications |
| [docs/dashboard-layout.md](docs/dashboard-layout.md) | Dashboard layout decisions |
| [docs/setup.md](docs/setup.md) | Local setup instructions |
| [docs/thinking-process.md](docs/thinking-process.md) | Key technical decisions |
| [docs/future-scope.md](docs/future-scope.md) | Planned extensions |

