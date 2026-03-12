"""Animal welfare topic keywords and helper functions."""

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "factory_farming": [
        "factory farm", "factory farming", "industrial farming",
        "battery cage", "caged hens", "gestation crate", "feedlot",
        "slaughterhouse", "pig farming", "chicken farming", "broiler",
        "intensive farming", "confined animal feeding",
        "livestock", "cattle farm", "poultry farm", "meat production",
        "animal husbandry", "abattoir", "henhouse", "hog farm",
    ],
    "animal_testing": [
        "animal testing", "animal experimentation", "vivisection",
        "lab animals", "laboratory animals", "animal research",
        "cosmetics testing", "drug testing on animals", "animal trials",
        "animal model", "primate research", "mouse model",
    ],
    "wildlife": [
        "wildlife", "poaching", "ivory trade", "wildlife trafficking",
        "habitat destruction", "endangered species", "biodiversity",
        "illegal wildlife trade", "wildlife conservation", "trophy hunting",
        "deforestation", "animal extinction", "rhino horn", "elephant tusk",
        # Broader conservation terms (multi-word to avoid false positives)
        "wildlife conservation", "nature conservation", "species conservation",
        "ecosystem collapse", "ecological crisis", "habitat loss",
        "extinct species", "bird migration", "breeding season", "nesting site",
        "nature reserve", "national park", "marine sanctuary",
        "protected area", "ecological damage",
        # Common animal groups
        "mammal", "reptile", "amphibian", "primate", "marine life",
        "migratory bird", "bird of prey", "songbird", "seabird",
        # Specific animals (removed ambiguous short words like fox/lion/seal/cod/crane)
        "hedgehog", "badger", "deer", "wolf", "polar bear",
        "whale", "dolphin", "shark", "penguin", "otter",
        "eagle", "falcon", "hawk", "parrot",
        "butterfly", "bee colony", "coral reef", "turtle", "tortoise",
        "elephant", "tiger", "gorilla", "orangutan", "chimpanzee",
        "rhinoceros", "rhino", "leopard", "panda",
        "koala", "kangaroo", "arctic fox",
        "salmon", "sturgeon",
    ],
    "pet_welfare": [
        "animal cruelty", "pet abuse", "dog fighting", "cockfighting",
        "puppy mill", "animal neglect", "companion animal", "pet welfare",
        "stray animals", "animal hoarding", "dogfighting",
        "animal shelter", "animal rescue", "pet adoption",
        "spay", "neuter", "kennel", "veterinary",
        "animal sanctuary", "horse rescue", "cat rescue", "dog rescue",
    ],
    "animal_policy": [
        "animal welfare law", "animal rights bill", "animal protection act",
        "animal welfare policy", "animal legislation", "animal ban",
        "animal welfare regulation", "animal rights legislation",
        "animal welfare", "animal rights", "animal protection",
        "RSPCA", "ASPCA", "humane society", "WWF",
        "animal welfare act", "endangered species act",
    ],
    "veganism": [
        "vegan", "veganism", "plant-based", "plant based",
        "meat industry", "dairy industry", "animal agriculture",
        "meatless", "animal-free", "cruelty-free food",
        "lab-grown meat", "cultured meat", "meat alternative",
        "dairy-free", "meat consumption",
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
