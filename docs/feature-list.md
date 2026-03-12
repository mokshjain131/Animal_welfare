# Feature List

---

## Section 1 — Core Dashboard Features

---

### F1 — Overview Metrics Bar

| | |
|---|---|
| **Priority** | Must Have |
| **Chart Type** | 4 stat cards |

**Displays:**
- Articles analyzed today
- Average sentiment score with +/- change vs yesterday
- Number of active animal welfare topics detected
- Misinformation alert count
- Story spike banner shown above metrics if active

---

### F2 — Sentiment Trend Over Time

| | |
|---|---|
| **Priority** | Must Have |
| **Chart Type** | Line chart (Recharts `LineChart`) |

**Features:**
- Daily average sentiment score on Y-axis over time
- Filterable by topic category
- Hover tooltips showing date, score, and article count
- Selectable time range: 7 days / 30 days / all time
- Positive values shown in green, negative in red

---

### F3 — Topic Distribution

| | |
|---|---|
| **Priority** | Must Have |
| **Chart Type** | Bar chart (Recharts `BarChart`) |

**Features:**
- Article count per topic for current day or week
- Topics: Factory Farming, Wildlife, Animal Testing, Pet Welfare, Animal Policy, Veganism
- Color-coded bars per topic category
- Sortable by volume descending

---

### F4 — Narrative Shift Detector

| | |
|---|---|
| **Priority** | **Most Important** |
| **Chart Type** | Stacked area chart (Recharts `AreaChart`) |

**Features:**
- Topic mention volume tracked over time
- Directly addresses the problem statement requirement for narrative shift tracking
- Computed as: `topic_mentions_per_day / total_articles_that_day`
- Spike markers overlaid when a topic crosses the alert threshold
- Shows when a topic surges — e.g. *"Factory Farming +210% in 24h"*

---

### F5 — Story Spike Detector

| | |
|---|---|
| **Priority** | High Impact |
| **Chart Type** | Alert banner |

**Logic:** `topic_mentions_today > 2× 7-day rolling average`

**Features:**
- Displays: *"Spike detected: Factory Farming — coverage up 210% in last 24 hours"*
- Appears as a prominent banner at the top of the dashboard when active
- Spike history logged in database for later review
- Computed by Summary Aggregator every 30 minutes

---

### F6 — Latest Articles Feed

| | |
|---|---|
| **Priority** | Must Have |
| **Chart Type** | Scrollable list |

**Features:**
- Headline, source name, and published timestamp
- Topic classification badge per article
- Sentiment score with color indicator
- Misinformation flag shown inline if applicable
- Click-through to original article URL
- Filterable by topic, sentiment polarity, and source

---

## Section 2 — Intelligence & Analysis Features

---

### F7 — Misinformation Alerts Panel

| | |
|---|---|
| **Priority** | **Most Impressive to Reviewers** |
| **Chart Type** | Review queue table |

**Features:**
- Articles flagged by HuggingFace with high suspicion scores
- Framed as *"flagged for review"* — never as *"confirmed misinformation"*
- Shows headline, source, confidence score, and reason for flagging
- Sorted by confidence score descending
- Dismiss or confirm buttons for analyst workflow
- Link to original article for manual verification

---

### F8 — Trending Keywords

| | |
|---|---|
| **Priority** | Impressive Extra |
| **Chart Type** | Ranked keyword list |

**Features:**
- Top 10 trending keyphrases from the last 3 days
- YAKE extracts statistical keyphrases per article at ingestion time
- TF-IDF computes corpus-level statistical spikes vs 7-day baseline every 30 minutes
- Only animal-welfare-relevant phrases are shown (filtered by ~100-word vocabulary)
- Trending up or down indicator compared to baseline
- Topic category label and article count per phrase

---

### F9 — Top Entities Mentioned

| | |
|---|---|
| **Priority** | High Value |
| **Chart Type** | Ranked lists (spaCy NER) |

**Features:**
- **Top organisations:** WWF, PETA, USDA, etc.
- **Top locations:** countries, states, regions
- **Top animal species:** pigs, chickens, elephants, etc.
- Each entity links to its relevant articles in the feed
- Extracted by spaCy `ORG`, `GPE`, and `ANIMAL` entity types — top 5 per category

---

### F10 — Source Sentiment Comparison

| | |
|---|---|
| **Priority** | Added Value |
| **Chart Type** | Horizontal bar chart (Recharts `BarChart`) |

**Features:**
- Average sentiment score broken down by top 10 news sources by volume
- Reveals which outlets consistently frame animal welfare positively or negatively
- Color coded: green for positive, red for negative
- Click a source to filter the Latest Articles feed

---

## Section 3 — Backend Pipeline Features

---

### F11 — Multi-Source Ingestion

**Priority:** Core

| Source | Details |
|---|---|
| RSS Feeds | Broad outlet coverage, no API key required |
| NewsAPI | Keyword-targeted search across 80,000+ sources |
| Trafilatura | Full-text extraction from article URLs |
| Fallback | Uses `title + description` if scraping returns under 150 characters |

- URL-based deduplication check before any NLP processing

---

### F12 — Relevance Gate

**Priority:** Core

- Weighted keyword scoring: title match = +2, body match = +1, minimum threshold = 2
- One title keyword is sufficient to pass; a single body mention is not
- Uses configurable keyword list per topic category (78 compound phrases, no bare generic terms)
- Prevents wasted compute on irrelevant content
- Rejected articles logged with score and matched keywords
- Keyword list updatable without code changes

---

### F13 — Scheduled Pipeline & Aggregator

**Priority:** Core

| Job | Schedule | Description |
|---|---|---|
| Ingestion + NLP | Every 15–30 min | Fetches, enriches, and saves new articles |
| Summary Aggregator | Every 30 min | Writes pre-computed rows to `daily_summaries` |
| Spike Detector | Every 30 min | Computes rolling averages, writes `spike_events` |
| TF-IDF Keywords | Every 30 min | Recomputes trending phrases from last 3 days, filtered for animal welfare relevance |

> All summary data is pre-computed so the dashboard **never runs slow raw aggregation queries**.
