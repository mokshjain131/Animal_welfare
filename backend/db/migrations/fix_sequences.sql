-- ============================================================
-- Fix auto-increment sequences after data migration.
-- Run this in Supabase SQL Editor.
-- ============================================================

-- Reset all SERIAL sequences to max(id) + 1

SELECT setval('articles_id_seq',        COALESCE((SELECT MAX(id) FROM articles), 0) + 1, false);
SELECT setval('sentiment_scores_id_seq', COALESCE((SELECT MAX(id) FROM sentiment_scores), 0) + 1, false);
SELECT setval('topics_id_seq',           COALESCE((SELECT MAX(id) FROM topics), 0) + 1, false);
SELECT setval('entities_id_seq',         COALESCE((SELECT MAX(id) FROM entities), 0) + 1, false);
SELECT setval('flagged_articles_id_seq', COALESCE((SELECT MAX(id) FROM flagged_articles), 0) + 1, false);
SELECT setval('keyphrases_id_seq',       COALESCE((SELECT MAX(id) FROM keyphrases), 0) + 1, false);
SELECT setval('trending_keywords_id_seq', COALESCE((SELECT MAX(id) FROM trending_keywords), 0) + 1, false);
SELECT setval('daily_summaries_id_seq',  COALESCE((SELECT MAX(id) FROM daily_summaries), 0) + 1, false);
SELECT setval('spike_events_id_seq',     COALESCE((SELECT MAX(id) FROM spike_events), 0) + 1, false);
