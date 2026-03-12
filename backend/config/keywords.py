"""Animal welfare topic keywords and helper functions.

Keywords are grouped by topic.  The relevance gate uses these to score
incoming articles — title matches are weighted higher than body-only matches.
Avoid single generic words that could match non-animal-welfare content
(e.g. plain "wildlife" or "biodiversity").
"""

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "factory_farming": [
        "factory farm", "factory farming", "industrial farming",
        "battery cage", "caged hens", "gestation crate", "feedlot",
        "slaughterhouse", "pig farming", "chicken farming", "broiler",
        "intensive farming", "confined animal feeding", "live export",
        "animal slaughter", "livestock welfare",
    ],
    "animal_testing": [
        "animal testing", "animal experimentation", "vivisection",
        "lab animals", "laboratory animals", "animal research",
        "cosmetics testing", "drug testing on animals", "animal trials",
    ],
    "wildlife": [
        "wildlife trafficking", "wildlife trade", "wildlife conservation",
        "wildlife protection", "wildlife poaching", "wildlife crime",
        "illegal wildlife", "wild animals",
        "poaching", "ivory trade", "trophy hunting",
        "endangered animal", "endangered species",
        "animal extinction", "rhino horn", "elephant tusk",
        "animal habitat", "species protection",
    ],
    "pet_welfare": [
        "animal cruelty", "animal abuse", "pet abuse",
        "dog fighting", "cockfighting", "dogfighting",
        "puppy mill", "animal neglect", "companion animal", "pet welfare",
        "stray animals", "animal hoarding", "animal rescue",
        "animal shelter", "animal suffering",
    ],
    "animal_policy": [
        "animal welfare", "animal rights", "animal protection",
        "animal welfare law", "animal rights bill", "animal protection act",
        "animal welfare policy", "animal legislation", "animal ban",
        "animal welfare regulation", "animal rights legislation",
    ],
    "veganism": [
        "vegan", "veganism", "plant-based", "plant based",
        "meat industry", "dairy industry", "animal agriculture",
        "meatless", "animal-free", "cruelty-free food",
    ],
}


def get_all_keywords() -> list[str]:
    """Return a flat list of every keyword across all topics."""
    return [kw for keywords in TOPIC_KEYWORDS.values() for kw in keywords]


def get_topic_labels() -> list[str]:
    """Return the list of topic category names."""
    return list(TOPIC_KEYWORDS.keys())


def detect_topic_from_keywords(text: str) -> str | None:
    """Simple fallback: return the topic with the most keyword matches, or None."""
    text_lower = text.lower()
    best_topic = None
    best_count = 0

    for topic, keywords in TOPIC_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_topic = topic

    return best_topic
