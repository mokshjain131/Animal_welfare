-- ============================================================
-- Supabase RPC functions for complex aggregate queries
-- Run this AFTER init.sql in the Supabase SQL Editor.
-- ============================================================

-- 1. Daily summary stats: per-topic article count + sentiment breakdown
CREATE OR REPLACE FUNCTION rpc_daily_summary_stats(
    p_topic TEXT,
    p_start TIMESTAMP,
    p_end   TIMESTAMP
)
RETURNS TABLE (
    total      BIGINT,
    avg_score  DOUBLE PRECISION,
    pos        BIGINT,
    neg        BIGINT,
    neu        BIGINT
) LANGUAGE sql STABLE AS $$
    SELECT
        count(a.id)                                                    AS total,
        avg(s.score)                                                   AS avg_score,
        count(*) FILTER (WHERE s.label = 'positive')                   AS pos,
        count(*) FILTER (WHERE s.label = 'negative')                   AS neg,
        count(*) FILTER (WHERE s.label = 'neutral')                    AS neu
    FROM articles a
    JOIN topics t        ON t.article_id = a.id
    JOIN sentiment_scores s ON s.article_id = a.id
    WHERE t.topic = p_topic
      AND a.published_at >= p_start
      AND a.published_at <  p_end;
$$;


-- 2. Topic volumes: article_count per topic over a date range
CREATE OR REPLACE FUNCTION rpc_topic_volumes(p_since DATE)
RETURNS TABLE (
    topic         TEXT,
    article_count BIGINT
) LANGUAGE sql STABLE AS $$
    SELECT
        ds.topic::TEXT,
        sum(ds.article_count)::BIGINT AS article_count
    FROM daily_summaries ds
    WHERE ds.date >= p_since
    GROUP BY ds.topic
    ORDER BY article_count DESC;
$$;


-- 3. Top entities by type
CREATE OR REPLACE FUNCTION rpc_top_entities(
    p_type  TEXT,
    p_since TIMESTAMP,
    p_limit INT
)
RETURNS TABLE (
    name  TEXT,
    count BIGINT
) LANGUAGE sql STABLE AS $$
    SELECT
        e.entity_text AS name,
        count(e.id)   AS count
    FROM entities e
    JOIN articles a ON a.id = e.article_id
    WHERE e.entity_type = p_type
      AND a.published_at >= p_since
    GROUP BY e.entity_text
    ORDER BY count DESC
    LIMIT p_limit;
$$;


-- 4. Source sentiment: avg sentiment + article count per source
CREATE OR REPLACE FUNCTION rpc_source_sentiment(
    p_since TIMESTAMP,
    p_limit INT
)
RETURNS TABLE (
    source_name   TEXT,
    article_count BIGINT,
    avg_sentiment DOUBLE PRECISION
) LANGUAGE sql STABLE AS $$
    SELECT
        a.source_name::TEXT      AS source_name,
        count(a.id)::BIGINT      AS article_count,
        avg(s.score)             AS avg_sentiment
    FROM articles a
    JOIN sentiment_scores s ON s.article_id = a.id
    WHERE a.published_at >= p_since
    GROUP BY a.source_name
    ORDER BY article_count DESC
    LIMIT p_limit;
$$;


-- 5. Overview metrics: today's articles, avg sentiment, etc.
CREATE OR REPLACE FUNCTION rpc_overview_metrics(
    p_today_start     TIMESTAMP,
    p_yesterday_start TIMESTAMP
)
RETURNS TABLE (
    articles_today         BIGINT,
    avg_sentiment_today    DOUBLE PRECISION,
    avg_sentiment_yesterday DOUBLE PRECISION,
    active_topics          BIGINT,
    misinfo_alerts         BIGINT
) LANGUAGE sql STABLE AS $$
    SELECT
        (SELECT count(id)  FROM articles WHERE published_at >= p_today_start)
            AS articles_today,
        (SELECT avg(s.score) FROM sentiment_scores s JOIN articles a ON a.id = s.article_id WHERE a.published_at >= p_today_start)
            AS avg_sentiment_today,
        (SELECT avg(s.score) FROM sentiment_scores s JOIN articles a ON a.id = s.article_id WHERE a.published_at >= p_yesterday_start AND a.published_at < p_today_start)
            AS avg_sentiment_yesterday,
        (SELECT count(DISTINCT topic) FROM daily_summaries WHERE date >= (p_today_start::date - interval '7 days')::date)
            AS active_topics,
        (SELECT count(id)  FROM flagged_articles WHERE is_reviewed = FALSE)
            AS misinfo_alerts;
$$;


-- 6. Recent articles with sentiment + topic (for /articles/recent)
CREATE OR REPLACE FUNCTION rpc_recent_articles(
    p_topic     TEXT DEFAULT NULL,
    p_sentiment TEXT DEFAULT NULL,
    p_source    TEXT DEFAULT NULL,
    p_limit     INT DEFAULT 20
)
RETURNS TABLE (
    id               INT,
    title            TEXT,
    url              TEXT,
    source_name      TEXT,
    published_at     TIMESTAMP,
    topic            TEXT,
    sentiment_label  TEXT,
    sentiment_score  DOUBLE PRECISION,
    is_flagged       BOOLEAN
) LANGUAGE sql STABLE AS $$
    SELECT
        a.id,
        a.title::TEXT,
        a.url::TEXT,
        a.source_name::TEXT,
        a.published_at,
        t.topic::TEXT        AS topic,
        s.label::TEXT        AS sentiment_label,
        s.score              AS sentiment_score,
        (EXISTS (SELECT 1 FROM flagged_articles f WHERE f.article_id = a.id)) AS is_flagged
    FROM articles a
    LEFT JOIN sentiment_scores s ON s.article_id = a.id
    LEFT JOIN topics t           ON t.article_id = a.id
    WHERE a.is_processed = TRUE
      AND (p_topic IS NULL     OR t.topic = p_topic)
      AND (p_sentiment IS NULL OR s.label = p_sentiment)
      AND (p_source IS NULL    OR a.source_name ILIKE '%' || p_source || '%')
    ORDER BY a.published_at DESC
    LIMIT p_limit;
$$;


-- 7. Flagged articles with article details
CREATE OR REPLACE FUNCTION rpc_flagged_articles(p_limit INT DEFAULT 20)
RETURNS TABLE (
    id              INT,
    title           TEXT,
    url             TEXT,
    source_name     TEXT,
    suspicion_score DOUBLE PRECISION,
    flag_reason     TEXT,
    published_at    TIMESTAMP
) LANGUAGE sql STABLE AS $$
    SELECT
        a.id,
        a.title::TEXT,
        a.url::TEXT,
        a.source_name::TEXT,
        f.suspicion_score,
        f.flag_reason::TEXT,
        a.published_at
    FROM flagged_articles f
    JOIN articles a ON a.id = f.article_id
    WHERE f.is_reviewed = FALSE
    ORDER BY f.suspicion_score DESC
    LIMIT p_limit;
$$;


-- 8. Keyphrase counts for trending computation
CREATE OR REPLACE FUNCTION rpc_keyphrase_counts(p_since TIMESTAMP)
RETURNS TABLE (
    phrase TEXT,
    cnt    BIGINT
) LANGUAGE sql STABLE AS $$
    SELECT
        lower(k.phrase) AS phrase,
        count(*)        AS cnt
    FROM keyphrases k
    JOIN articles a ON a.id = k.article_id
    WHERE a.published_at >= p_since
    GROUP BY lower(k.phrase);
$$;
