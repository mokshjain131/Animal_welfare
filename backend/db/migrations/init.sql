-- ============================================================
-- Animal Welfare News Sentiment Tracker — initial schema
-- Mirrors backend/db/models.py exactly.
-- Mounted into the Postgres container via docker-compose
-- so it runs automatically on first launch.
-- ============================================================

-- Articles
CREATE TABLE IF NOT EXISTS articles (
    id            SERIAL PRIMARY KEY,
    url           VARCHAR(2048) NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    full_text     TEXT,
    source_name   VARCHAR(255) NOT NULL,
    source_type   VARCHAR(50)  NOT NULL,
    published_at  TIMESTAMP    NOT NULL,
    created_at    TIMESTAMP    DEFAULT NOW(),
    is_processed  BOOLEAN      DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_articles_url          ON articles (url);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles (published_at);
CREATE INDEX IF NOT EXISTS idx_articles_is_processed ON articles (is_processed);


-- Sentiment scores
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id          SERIAL PRIMARY KEY,
    article_id  INTEGER NOT NULL REFERENCES articles(id),
    label       VARCHAR(20) NOT NULL,
    score       FLOAT       NOT NULL,
    created_at  TIMESTAMP   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_article ON sentiment_scores (article_id);


-- Topic classifications
CREATE TABLE IF NOT EXISTS topics (
    id          SERIAL PRIMARY KEY,
    article_id  INTEGER      NOT NULL REFERENCES articles(id),
    topic       VARCHAR(100) NOT NULL,
    confidence  FLOAT        NOT NULL,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topics_topic ON topics (topic);


-- Named entities
CREATE TABLE IF NOT EXISTS entities (
    id          SERIAL PRIMARY KEY,
    article_id  INTEGER      NOT NULL REFERENCES articles(id),
    entity_text VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50)  NOT NULL,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_article ON entities (article_id);


-- Flagged articles (misinfo review queue)
CREATE TABLE IF NOT EXISTS flagged_articles (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER      NOT NULL UNIQUE REFERENCES articles(id),
    suspicion_score FLOAT        NOT NULL,
    flag_reason     VARCHAR(500),
    is_reviewed     BOOLEAN      DEFAULT FALSE,
    is_confirmed    BOOLEAN,
    created_at      TIMESTAMP    DEFAULT NOW(),
    reviewed_at     TIMESTAMP
);


-- Keyphrases per article
CREATE TABLE IF NOT EXISTS keyphrases (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER      NOT NULL REFERENCES articles(id),
    phrase          VARCHAR(500) NOT NULL,
    relevance_score FLOAT        NOT NULL,
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keyphrases_article ON keyphrases (article_id);


-- Trending keywords (overwritten every 30 min)
CREATE TABLE IF NOT EXISTS trending_keywords (
    id              SERIAL PRIMARY KEY,
    phrase          VARCHAR(500) NOT NULL,
    score           FLOAT        NOT NULL,
    article_count   INTEGER      NOT NULL,
    trend_direction VARCHAR(10)  NOT NULL,
    topic           VARCHAR(100),
    computed_at     TIMESTAMP    DEFAULT NOW()
);


-- Daily summaries (pre-computed rollups)
CREATE TABLE IF NOT EXISTS daily_summaries (
    id              SERIAL PRIMARY KEY,
    date            DATE         NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    article_count   INTEGER      NOT NULL,
    avg_sentiment   FLOAT        NOT NULL,
    positive_count  INTEGER      NOT NULL,
    negative_count  INTEGER      NOT NULL,
    neutral_count   INTEGER      NOT NULL,
    created_at      TIMESTAMP    DEFAULT NOW(),
    UNIQUE (date, topic)
);

CREATE INDEX IF NOT EXISTS idx_daily_date_topic ON daily_summaries (date, topic);


-- Spike events
CREATE TABLE IF NOT EXISTS spike_events (
    id            SERIAL PRIMARY KEY,
    topic         VARCHAR(100) NOT NULL,
    spike_date    DATE         NOT NULL,
    article_count INTEGER      NOT NULL,
    weekly_avg    FLOAT        NOT NULL,
    multiplier    FLOAT        NOT NULL,
    is_active     BOOLEAN      DEFAULT TRUE,
    detected_at   TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_spike_active ON spike_events (is_active);
