Why you chose this tech stack over alternatives
Why RSS and NewsAPI together instead of one or the other
Why spaCy and HuggingFace together instead of just one
Why you skipped TimescaleDB for v1 but designed the schema for it
Why Trafilatura over newspaper3k
Why you dropped Redis for now
Why one repo instead of multiple
Why APScheduler instead of cron
How you thought about the misinformation flagging problem and why you framed it as "flagged for review" rather than a verdict
What you would build next if you had more time



Problem statement:
While researching about the domain “animal welfare” I discovered that any general sentiment of a news article can be different in the context of animal welfare. We need a robust system which can access these new updates and trends from a lens of movement strategists.

Existing solution:
While researching for existing solutions for this problem I discovered that there are a lot of News sentiment analysis pipelines, Commercial media monitoring platforms and APIs for providing sentiment annotated news. But there is none which address the specific niche of animal welfare and no pipeline which provides all sentiment analysis, tracking functionalities and visualization for this niche. 
There are many services available which I can use in my pipeline.

Tech stack:
Python backend: best for pipelines and amazing support for NLP through libraries and community support. Compared to node js which has weak support for NLP. I will be using FastAPI as a python backend because of easy integration with hugging face and spacy and other services. FastAPI also has automatic documentation.

Model:


Ingestion:
RSS + NewsAPI + Scraper

Database:
PostgreSQL because of its small dataset size. In future with continuous live field and large historical news stream TimeScaleDB can be introduced to enable hypertables and continuous aggregates.

Frontend and Visualization: 
React + Recharts. Recharts is built on react and offers low complexity while building the pipeline. D3 can be an upgrade if there is a need for highly custom visualization.

Caching:
Redis adds additional complexity. For now there is no need for it. If the UI feels sluggish then it can be used.

Scheduler:
APScheduler is easily integratable with FastAPI and lives with the python script. It can run the whole pipeline in a fixed interval (15 - 30 mins). Cron job can be used alternatively.

Features:


System architecture:


Data Flow:





Future Scope:
