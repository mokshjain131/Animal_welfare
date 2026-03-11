"""NLP Pipeline orchestrator — runs all NLP steps on articles and saves results."""

import logging

from supabase import Client

from nlp.spacy_processor import process_article as spacy_process
from nlp.sentiment import analyze_sentiment
from nlp.topic_classifier import classify_topic
from nlp.misinfo_detector import score_misinfo
from nlp.keybert_extractor import extract_keyphrases

logger = logging.getLogger(__name__)


def process_article(article: dict, sb: Client) -> None:
    """Run full NLP pipeline on one article dict and save all results to Supabase.

    Input : article — dict with keys: id, title, full_text, url
            sb — Supabase client
    Output: None (writes to sentiment_scores, topics, entities, flagged_articles, keyphrases)
    """
    article_id = article["id"]
    text = article.get("full_text") or article.get("title") or ""
    if not text.strip():
        logger.warning("Article %d has no text — skipping NLP", article_id)
        sb.table("articles").update({"is_processed": True}).eq("id", article_id).execute()
        return

    try:
        # 1. spaCy: entities + cleaned text
        spacy_result = spacy_process(text)
        cleaned_text = spacy_result["cleaned_text"]
        entities = spacy_result["entities"]

        if entities:
            entity_rows = [
                {
                    "article_id": article_id,
                    "entity_text": ent["entity_text"][:500],
                    "entity_type": ent["entity_type"],
                }
                for ent in entities
            ]
            sb.table("entities").insert(entity_rows).execute()

        # 2. Sentiment analysis
        sentiment = analyze_sentiment(cleaned_text)
        sb.table("sentiment_scores").insert({
            "article_id": article_id,
            "label": sentiment["label"],
            "score": sentiment["score"],
        }).execute()

        # 3. Topic classification
        topic = classify_topic(cleaned_text)
        sb.table("topics").insert({
            "article_id": article_id,
            "topic": topic["topic"],
            "confidence": topic["confidence"],
        }).execute()

        # 4. Misinformation detection
        misinfo = score_misinfo(cleaned_text)
        if misinfo["should_flag"]:
            sb.table("flagged_articles").insert({
                "article_id": article_id,
                "suspicion_score": misinfo["suspicion_score"],
                "flag_reason": misinfo["flag_reason"],
            }).execute()

        # 5. Keyphrase extraction
        keyphrases = extract_keyphrases(cleaned_text)
        if keyphrases:
            kp_rows = [
                {
                    "article_id": article_id,
                    "phrase": kp["phrase"][:500],
                    "relevance_score": kp["relevance_score"],
                }
                for kp in keyphrases
            ]
            sb.table("keyphrases").insert(kp_rows).execute()

    except Exception as e:
        logger.error("NLP pipeline error for article %d (%s): %s",
                      article_id, article.get("url", ""), e)

    # Always mark as processed — partial results beat infinite retries
    sb.table("articles").update({"is_processed": True}).eq("id", article_id).execute()


def process_unprocessed_articles(sb: Client) -> int:
    """Fetch all unprocessed articles and run NLP on each.

    Input : sb — Supabase client
    Output: int — number of articles processed
    """
    result = (
        sb.table("articles")
        .select("*")
        .eq("is_processed", False)
        .execute()
    )
    articles = result.data
    total = len(articles)

    if total == 0:
        logger.info("No unprocessed articles found")
        return 0

    logger.info("Processing %d unprocessed articles...", total)

    for i, article in enumerate(articles, 1):
        process_article(article, sb)

        if i % 10 == 0 or i == total:
            logger.info("Processed %d / %d articles", i, total)

    return total
