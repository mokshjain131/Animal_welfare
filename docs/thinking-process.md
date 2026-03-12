# Thinking Process

This document explains how the project was thought through in plain English: why certain tools were chosen, what problems came up during development, and how those problems were solved.

---

## 1. The core problem

The starting point was simple: regular news sentiment is not the same as animal-welfare sentiment.

For example, an article about a cruelty investigation, a farm-abuse expose, or a government crackdown on wildlife trafficking may sound negative in normal language. But from the point of view of an animal-welfare strategist, that same article could actually be positive because it represents enforcement, reform, or progress.

That changed the whole direction of the system. The goal was not just to collect news and attach a generic sentiment label. The goal was to build a tracker that reads news through an animal-welfare lens and helps someone understand:

- what topics are rising,
- whether the overall direction is good or bad for animals,
- which narratives are shifting,
- and what specific articles deserve attention.

---

## 2. Why this stack was chosen

### Python + FastAPI

Python made the most sense because the project is mostly a data and NLP pipeline. The ecosystem for this kind of work is much stronger in Python than in Node.js. FastAPI was a good fit because it is lightweight, easy to structure, and gives automatic API docs out of the box.

### RSS + NewsAPI + scraping

No single source was enough.

- **RSS** is free and reliable, but it only gives whatever each outlet publishes in its feeds.
- **NewsAPI** helps with keyword-based discovery across many sources, but it has quota limits.
- **Scraping** is needed because feed descriptions are often too short for proper NLP.

Putting them together gave better coverage than relying on one source alone.

### spaCy + HuggingFace

spaCy and HuggingFace solve different problems.

- **spaCy** is good for fast local text cleaning and entity extraction.
- **HuggingFace** is better for classification tasks like topic detection, sentiment, and misinformation scoring.

Using both kept the system practical. spaCy handled the lighter NLP tasks cheaply and quickly, while HuggingFace handled the harder judgment calls.

### PostgreSQL / Supabase

The dataset size for v1 is not large enough to justify a more complex database setup. PostgreSQL is more than enough for now, and Supabase makes hosting and remote access easy.

The schema was still designed in a way that can later move to TimescaleDB if the project grows into long-running historical monitoring.

### React + Recharts

The dashboard needed to be fast to build and easy to maintain. React is the most practical choice for that, and Recharts is enough for the kinds of visualisations needed here. D3 would only make sense if the visuals became much more custom later.

### APScheduler

For this version, APScheduler was the simplest way to keep the pipeline running on a fixed interval inside the backend app itself. It avoided the overhead of setting up separate workers or external schedulers too early.

---

## 3. The biggest design decision: sentiment had to be domain-aware

At first, a normal sentiment model seemed like the obvious choice. The original plan was to use `cardiffnlp/twitter-roberta-base-sentiment-latest`.

That turned out to be the wrong fit for this problem.

The issue was that generic sentiment tells you whether the writing sounds positive or negative in a general sense. It does not tell you whether the event is good or bad for animals. In this project, that difference matters a lot.

### What went wrong

The generic sentiment scores looked confident, but they were not actually useful for animal-welfare analysis. The average sentiment number also became misleading, because it mostly reflected model confidence rather than real directional meaning.

### What was done instead

The sentiment step was redesigned using `facebook/bart-large-mnli` with zero-shot labels:

- `positive for animal welfare`
- `negative for animal welfare`
- `neutral regarding animal welfare`

This made the score directional:

- `1.0` means strongly positive for animal welfare
- `0.5` means neutral
- `0.0` means strongly negative for animal welfare

That change made `AVG(score)` useful and made the dashboard much more honest.

---

## 4. Challenge: too many irrelevant articles were getting through

One of the biggest practical problems came from the relevance gate.

The first version used a simple rule: if any keyword appeared anywhere in the title or body, the article was treated as relevant.

### What went wrong

This sounded reasonable, but in practice it was too loose. It let in a lot of irrelevant content, including articles that only mentioned one vague word in passing. Examples included:

- mining or environmental articles that mentioned habitat,
- geography stories that mentioned wildlife,
- unrelated food or travel content with casual animal words.

This polluted the database and made later analysis worse.

### What was done instead

Two fixes were made.

#### 1. The keyword list was tightened

Generic words were removed, including:

- `wildlife`
- `biodiversity`
- `deforestation`
- `habitat destruction`

They were replaced with more specific phrases like:

- `wildlife trafficking`
- `wildlife trade`
- `wildlife conservation`
- `wildlife protection`
- `endangered animal`
- `animal rescue`
- `animal suffering`

#### 2. The relevance gate was changed to weighted scoring

Instead of a yes/no keyword match, the gate now scores articles like this:

- keyword in the **title** = +2
- keyword in the **body only** = +1
- minimum score to pass = **2**

This means one strong title match is enough, but one weak body mention is not.

That change made a major difference. The existing dataset was rechecked, and a large number of irrelevant articles were removed.

---

## 5. Challenge: trending keywords were surfacing nonsense

The trending panel was another place where the first version looked acceptable technically but was not useful in practice.

### What went wrong

The keyphrase extractor could surface statistically important phrases that had nothing to do with animal welfare. The spike logic then treated those phrases as trends.

So the dashboard started showing things like company names, place names, or random phrases that were only “trending” mathematically, not thematically.

### What caused it

This was not really a bug in the scoring. It was a scope problem. YAKE does not understand the domain. It simply finds phrases that stand out in text.

### What was done instead

Three improvements were made:

1. A broad **animal-welfare vocabulary filter** was added.
	- A trending phrase must now contain at least one animal-related or welfare-related term.

2. The recent window was widened from **24 hours to 3 days**.
	- This prevents the table from becoming empty or stale when article volume is low.

3. Old trending rows are now cleared **before** the early-return path.
	- This fixed stale data sticking around when there were no fresh results.

After that, the trending panel became much more useful.

---

## 6. Challenge: the NLP stack was too heavy for the project

The early approach relied more on local NLP packages and heavyweight model dependencies.

### What went wrong

Using local transformer-based tooling meant:

- large downloads,
- slower setup,
- more deployment friction,
- more room for environment problems.

This was especially true for the old KeyBERT setup, which pulled in `sentence-transformers`, `torch`, and model weights that were not ideal for a lightweight deployment.

### What was done instead

Two decisions simplified the stack a lot:

#### HuggingFace Inference API for classification

Sentiment, topic classification, and misinformation scoring all use API-based inference now. That means there is no need to ship large local transformer models with the backend.

#### YAKE for keyphrase extraction

KeyBERT was replaced with YAKE because it is simple, local, and lightweight. It does not need a GPU, model downloads, or a complicated setup.

This made the project easier to deploy and easier to explain.

---

## 7. Challenge: external APIs do not always return data in one consistent shape

Another real issue came from the HuggingFace inference responses.

### What went wrong

The code originally expected one response shape, but in practice the API could return either:

- a dictionary with `labels` and `scores`, or
- a list of `{label, score}` objects.

That caused parsing issues.

### What was done instead

Both `sentiment.py` and `topic_classifier.py` were updated to handle both formats safely. That removed a fragile assumption from the code.

---

## 8. Challenge: deployment should be easy, not fragile

The system needed to run locally and also deploy cleanly.

### Problems that came up

- CORS was too restrictive for deployment at first.
- Environment loading needed to work reliably regardless of the working directory.
- The app needed a clear health endpoint for hosting platforms.

### What was done

- CORS was opened to `allow_origins=["*"]` for simple frontend/backend connectivity.
- Settings were updated to resolve `.env` from the project root more reliably.
- The backend exposes `/health`, which is suitable for a health check.

These are small changes, but they make deployment much smoother.

---

## 9. Why some things were deliberately not added yet

### Redis

Redis was skipped because it would add another moving part before the project actually needed it. The API mostly reads from pre-computed tables already, so performance is acceptable without caching.

### TimescaleDB

TimescaleDB is attractive for long-term time-series analytics, but it would be unnecessary complexity for the current data volume. PostgreSQL is enough for now.

### Microservices / multiple repositories

Everything was kept in one repository because this project is still evolving quickly. Keeping backend, frontend, and docs together makes changes faster and easier to coordinate.

### D3 and highly custom visualisations

Recharts already covers the dashboard needs. Going deeper into D3 would increase effort without solving a real current problem.

---

## 10. Why misinformation is framed carefully

This part needed special care.

The system can estimate whether an article looks suspicious, but it should not claim that an article is definitely false. That would be too strong, and it would be easy to misuse.

So the design deliberately uses language like:

- **flagged for review**
- **suspicion score**
- **potentially misleading**

This keeps the tool useful without pretending it can replace human judgment.

---

## 11. What was learned from building this

The biggest lesson was that the technically easiest version is not always the right version.

A lot of the important fixes came from looking at real outputs and asking whether they made sense for the domain:

- Are these articles really about animal welfare?
- Does this sentiment score actually mean anything useful?
- Are these trending phrases helpful, or just statistically noisy?

Those questions led to the best improvements.

In other words, the project became better not just by adding more NLP, but by making the system more selective, more domain-aware, and more honest about what it knows.

---

## 12. If there was more time

The next steps would be:

1. Build a labelled animal-welfare dataset from reviewed articles
2. Fine-tune a domain-specific sentiment and topic model
3. Add analyst feedback tools for flagged articles
4. Improve source quality analysis and narrative tracking
5. Move to stronger historical analytics if the dataset grows large enough

---

## Final summary

This project started as a news monitoring dashboard, but the real challenge was not just collecting articles. The real challenge was teaching the system to care about the right things.

That meant:

- filtering out weak matches,
- judging sentiment from the right perspective,
- removing noisy trend signals,
- simplifying the deployment stack,
- and keeping the system transparent about its limits.

That is what turned it from a generic sentiment pipeline into something much closer to an animal-welfare intelligence tool.
