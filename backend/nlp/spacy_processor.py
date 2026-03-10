"""spaCy NER and text cleaning — loads model once, reuses across articles."""

import logging

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)

# ── Animal terms for custom ANIMAL entity detection ──────────────
ANIMAL_TERMS = {
    "pig", "pigs", "hog", "hogs", "swine",
    "chicken", "chickens", "hen", "hens", "rooster", "poultry",
    "cow", "cows", "cattle", "calf", "calves", "bull", "bulls",
    "sheep", "lamb", "lambs", "goat", "goats",
    "horse", "horses", "pony", "ponies",
    "dog", "dogs", "puppy", "puppies",
    "cat", "cats", "kitten", "kittens",
    "elephant", "elephants",
    "dolphin", "dolphins", "whale", "whales",
    "tiger", "tigers", "lion", "lions", "leopard", "leopards",
    "rhino", "rhinoceros", "gorilla", "gorillas", "chimpanzee",
    "bear", "bears", "wolf", "wolves", "fox", "foxes",
    "rabbit", "rabbits", "deer", "monkey", "monkeys", "primate", "primates",
}

# ── Allowed spaCy entity labels ─────────────────────────────────
ALLOWED_LABELS = {"ORG", "GPE", "LOC"}

# ── Load model once at import time ───────────────────────────────
_nlp: Language | None = None


def load_spacy_model() -> Language:
    """Load spaCy en_core_web_sm once and cache it.

    Input : None
    Output: spacy.Language model
    """
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded: en_core_web_sm")
    return _nlp


def extract_entities(text: str, nlp: Language) -> list[dict]:
    """Run NER on text. Return orgs, locations, and animal terms.

    Input : text — article full_text or cleaned_text
            nlp  — spaCy Language model
    Output: list of dicts with keys: entity_text, entity_type ("ORG", "GPE", "ANIMAL")
    """
    doc = nlp(text[:100_000])  # cap input to avoid memory issues
    seen: set[tuple[str, str]] = set()
    entities: list[dict] = []

    # Standard NER entities (ORG, GPE, LOC → mapped to GPE)
    for ent in doc.ents:
        if ent.label_ in ALLOWED_LABELS:
            etype = "GPE" if ent.label_ == "LOC" else ent.label_
            key = (ent.text.strip(), etype)
            if key not in seen:
                seen.add(key)
                entities.append({"entity_text": ent.text.strip(), "entity_type": etype})

    # Custom animal detection via token matching
    text_lower = text.lower()
    for term in ANIMAL_TERMS:
        if term in text_lower:
            key = (term, "ANIMAL")
            if key not in seen:
                seen.add(key)
                entities.append({"entity_text": term, "entity_type": "ANIMAL"})

    return entities


def clean_text(text: str, nlp: Language) -> str:
    """Clean article text — remove punctuation-only tokens, strip whitespace.

    Input : text — raw article text
            nlp  — spaCy Language model
    Output: cleaned text string
    """
    doc = nlp(text[:100_000])
    cleaned_tokens = [
        token.text for token in doc
        if not token.is_punct and not token.is_space
    ]
    return " ".join(cleaned_tokens).strip()


def process_article(text: str) -> dict:
    """Run all spaCy processing on one article.

    Input : text — article full_text
    Output: {"cleaned_text": str, "entities": list[dict]}
    """
    nlp = load_spacy_model()
    entities = extract_entities(text, nlp)
    cleaned = clean_text(text, nlp)
    return {"cleaned_text": cleaned, "entities": entities}
