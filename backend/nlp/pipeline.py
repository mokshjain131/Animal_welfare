"""NLP Pipeline orchestrator — runs all NLP steps on articles and saves results."""

import logging

from sqlalchemy.orm import Session

from db.models import (
    Article, SentimentScore, TopicClassification,
    Entity, FlaggedArticle, Keyphrase,
)
from nlp.spacy_processor import process_article as spacy_process
from nlp.sentiment import analyze_sentiment
from nlp.topic_classifier import classify_topic
from nlp.misinfo_detector import score_misinfo
from nlp.keybert_extractor import extract_keyphrases

logger = logging.getLogger(__name__)


def process_article(article: Article, db: Session) -> None:
    """Run full NLP pipeline on one article and save all results to DB.

    Input : article — SQLAlchemy Article row (must have id, full_text)
            db — SQLAlchemy session
    Output: None (writes to sentiment_scores, topics, entities, flagged_articles, keyphrases)

    Steps:
    1. spaCy  → entities + cleaned text
    2. Sentiment → label + score
    3. Topic → topic + confidence
    4. Misinfo → suspicion score + flag
    5. KeyBERT → keyphrases
    6. Mark article as processed
    """
    text = article.full_text or article.title or ""
    if not text.strip():
        logger.warning("Article %d has no text — skipping NLP", article.id)
        article.is_processed = True
        return

    try:
        # 1. spaCy: entities + cleaned text
        spacy_result = spacy_process(text)
        cleaned_text = spacy_result["cleaned_text"]
        entities = spacy_result["entities"]

        for ent in entities:
            db.add(Entity(
                article_id=article.id,
                entity_text=ent["entity_text"][:500],
                entity_type=ent["entity_type"],
            ))

        # 2. Sentiment analysis
        sentiment = analyze_sentiment(cleaned_text)
        db.add(SentimentScore(
            article_id=article.id,
            label=sentiment["label"],
            score=sentiment["score"],
        ))

        # 3. Topic classification
        topic = classify_topic(cleaned_text)
        db.add(TopicClassification(
            article_id=article.id,
            topic=topic["topic"],
            confidence=topic["confidence"],
        ))

        # 4. Misinformation detection
        misinfo = score_misinfo(cleaned_text)
        if misinfo["should_flag"]:
            db.add(FlaggedArticle(
                article_id=article.id,
                suspicion_score=misinfo["suspicion_score"],
                flag_reason=misinfo["flag_reason"],
            ))

        # 5. Keyphrase extraction
        keyphrases = extract_keyphrases(cleaned_text)
        for kp in keyphrases:
            db.add(Keyphrase(
                article_id=article.id,
                phrase=kp["phrase"][:500],
                relevance_score=kp["relevance_score"],
            ))

    except Exception as e:
        logger.error("NLP pipeline error for article %d (%s): %s", article.id, article.url, e)

    # Always mark as processed — partial results beat infinite retries
    article.is_processed = True


def process_unprocessed_articles(db: Session) -> int:
    """Fetch all unprocessed articles and run NLP on each.

    Input : db — SQLAlchemy session
    Output: int — number of articles processed
    """
    articles = db.query(Article).filter(Article.is_processed == False).all()
    total = len(articles)

    if total == 0:
        logger.info("No unprocessed articles found")
        return 0

    logger.info("Processing %d unprocessed articles...", total)

    for i, article in enumerate(articles, 1):
        process_article(article, db)
        db.commit()

        if i % 10 == 0 or i == total:
            logger.info("Processed %d / %d articles", i, total)

    return total
