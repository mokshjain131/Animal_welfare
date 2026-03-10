"""Animal welfare topic keywords and helper functions."""

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "factory_farming": [
        "factory farm", "factory farming", "industrial farming",
        "battery cage", "caged hens", "gestation crate", "feedlot",
        "slaughterhouse", "pig farming", "chicken farming", "broiler",
        "intensive farming", "confined animal feeding",
    ],
    "animal_testing": [
        "animal testing", "animal experimentation", "vivisection",
        "lab animals", "laboratory animals", "animal research",
        "cosmetics testing", "drug testing on animals", "animal trials",
    ],
    "wildlife": [
        "wildlife", "poaching", "ivory trade", "wildlife trafficking",
        "habitat destruction", "endangered species", "biodiversity",
        "illegal wildlife trade", "wildlife conservation", "trophy hunting",
        "deforestation", "animal extinction", "rhino horn", "elephant tusk",
    ],
    "pet_welfare": [
        "animal cruelty", "pet abuse", "dog fighting", "cockfighting",
        "puppy mill", "animal neglect", "companion animal", "pet welfare",
        "stray animals", "animal hoarding", "dogfighting",
    ],
    "animal_policy": [
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
