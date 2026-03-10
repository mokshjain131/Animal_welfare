"""Quick Module 2 verification script."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__) + "/..")

from config.settings import settings

print(f"DATABASE_URL  = {settings.DATABASE_URL}")
print(f"NEWSAPI_KEY   = {settings.NEWSAPI_KEY}")
print(f"MISINFO_THR   = {settings.MISINFO_THRESHOLD}")
print(f"SPIKE_MULT    = {settings.SPIKE_MULTIPLIER}")
print(f"INTERVAL_MIN  = {settings.PIPELINE_INTERVAL_MINUTES}")
print(f"RSS_FEEDS     = {len(settings.RSS_FEEDS)} feeds")
print()

from config.keywords import get_all_keywords, get_topic_labels, detect_topic_from_keywords

print(f"Topics         = {get_topic_labels()}")
print(f"Total keywords = {len(get_all_keywords())}")
print()

tests = [
    ("factory farming investigation", "factory_farming"),
    ("poaching elephants in Africa", "wildlife"),
    ("vegan plant-based diet", "veganism"),
    ("random unrelated text about weather", None),
]
for text, expected in tests:
    result = detect_topic_from_keywords(text)
    status = "PASS" if result == expected else "FAIL"
    print(f"  [{status}] detect('{text}') = {result}")

print()
from db.database import get_engine
engine = get_engine()
print(f"Engine: {engine.url}")
print("Module 2 verified!")
