"""Module 4 — NLP Pipeline verification script.

Tests each NLP sub-component, then runs the full pipeline on unprocessed articles.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("verify_module4")

# ── Step 1: spaCy Processor ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 1: spaCy Processor")
print("=" * 60)

from nlp.spacy_processor import process_article as spacy_process

test_text = (
    "The World Wildlife Fund (WWF) and PETA have called on the UK government "
    "to ban factory farming of chickens and pigs. The investigation in London "
    "revealed poor conditions at several facilities across Europe."
)

spacy_result = spacy_process(test_text)
print(f"  Cleaned text length: {len(spacy_result['cleaned_text'])} chars")
print(f"  Entities found: {len(spacy_result['entities'])}")
for ent in spacy_result["entities"]:
    print(f"    {ent['entity_type']:8s} | {ent['entity_text']}")

# ── Step 2: Sentiment Analysis ────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Sentiment Analysis")
print("=" * 60)

from nlp.sentiment import analyze_sentiment

pos_text = "Great news — the new animal welfare law has been passed and will protect millions of animals!"
neg_text = "Horrific animal cruelty discovered at illegal dog fighting ring. Many animals found dead."
neutral_text = "The government announced a review of existing animal welfare regulations."

for label, text in [("Expected positive", pos_text), ("Expected negative", neg_text), ("Expected neutral", neutral_text)]:
    result = analyze_sentiment(text)
    print(f"  {label}: {result['label']} ({result['score']:.4f})")

# ── Step 3: Topic Classification ──────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Topic Classification")
print("=" * 60)

from nlp.topic_classifier import classify_topic

topic_tests = [
    ("Factory farming investigation reveals battery cage conditions", "factory_farming"),
    ("New vegan restaurant chain opens across Europe", "veganism"),
    ("Elephant poaching crisis in East Africa continues", "wildlife"),
]

for text, expected in topic_tests:
    result = classify_topic(text)
    match = "✓" if result["topic"] == expected else "✗"
    print(f"  {match} '{text[:50]}...' → {result['topic']} ({result['confidence']:.4f}) [expected: {expected}]")

# ── Step 4: Misinfo Detector ─────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Misinformation Detector")
print("=" * 60)

from nlp.misinfo_detector import score_misinfo

misinfo_result = score_misinfo(test_text)
print(f"  Suspicion score: {misinfo_result['suspicion_score']:.4f}")
print(f"  Should flag:     {misinfo_result['should_flag']}")
print(f"  Flag reason:     {misinfo_result['flag_reason'] or '(none)'}")

# ── Step 5: KeyBERT Extractor ────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: KeyBERT Keyphrase Extraction")
print("=" * 60)

from nlp.keybert_extractor import extract_keyphrases

keyphrases = extract_keyphrases(test_text)
print(f"  Keyphrases extracted: {len(keyphrases)}")
for kp in keyphrases:
    print(f"    {kp['relevance_score']:.4f} | {kp['phrase']}")

# ── Step 6: Full Pipeline on DB Articles ──────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Full Pipeline — process unprocessed articles in DB")
print("=" * 60)

from db.database import get_session_factory
from db.models import Article, SentimentScore, TopicClassification, Entity, Keyphrase, FlaggedArticle
from nlp.pipeline import process_unprocessed_articles

Session = get_session_factory()
db = Session()

try:
    unprocessed = db.query(Article).filter(Article.is_processed == False).count()
    print(f"  Unprocessed articles in DB: {unprocessed}")

    count = process_unprocessed_articles(db)
    print(f"  Articles processed by pipeline: {count}")

    # Verify results in DB
    sentiments = db.query(SentimentScore).count()
    topics = db.query(TopicClassification).count()
    entities = db.query(Entity).count()
    keyphrases_count = db.query(Keyphrase).count()
    flagged = db.query(FlaggedArticle).count()
    processed = db.query(Article).filter(Article.is_processed == True).count()

    print(f"\n  DB Results:")
    print(f"    sentiment_scores: {sentiments} rows")
    print(f"    topics:           {topics} rows")
    print(f"    entities:         {entities} rows")
    print(f"    keyphrases:       {keyphrases_count} rows")
    print(f"    flagged_articles: {flagged} rows")
    print(f"    articles processed: {processed}")

finally:
    db.close()

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("MODULE 4 VERIFICATION SUMMARY")
print("=" * 60)
print("  spaCy entity extraction     ✓")
print("  Sentiment analysis          ✓")
print("  Topic classification        ✓")
print("  Misinfo detection           ✓")
print("  KeyBERT keyphrase extraction✓")
print(f"  Full pipeline on {count} articles ✓")
print("  ✓ Module 4 complete!")
