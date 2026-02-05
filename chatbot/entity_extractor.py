# Rule-based entity extraction module.
# This file is responsible for extracting structured entities such as
# facilities, dates, and priority levels from raw user text.

import re

# List of supported facility names that may appear in user messages
FACILITIES = [
    "آسانسور", "استخر", "سالن", "باشگاه", "برق", "آب", "پارکینگ", "انباری",
    "روف گاردن", "لابی", "درب", "دوربین", "آیفون"
]

# Regular expression patterns for detecting date-related expressions
DATE_PATTERNS = [
    r"\bامروز\b",
    r"\bفردا\b",
    r"\bپس\s?فردا\b",
    r"\bشنبه\b|\bیکشنبه\b|\bدوشنبه\b|\bسه\s?شنبه\b|\bچهارشنبه\b|\bپنجشنبه\b|\bجمعه\b",
]

# Mapping of priority levels to indicative keywords
PRIORITY_WORDS = {
    "urgent": ["فوری", "خیلی فوری", "ضروری", "اورژانسی"],
    "high": ["مهم", "سریع", "هرچی زودتر"],
    "medium": ["عادی", "معمولی"],
    "low": ["بعداً", "عجله ندارم"]
}

def extract_entities(text: str):
    """
    Extract entities from input text using simple string matching
    and regular expressions.

    Returns a dictionary containing detected entities.
    """
    entities = {}

    # 1) Facility extraction using keyword matching
    found_facilities = []
    for f in FACILITIES:
        if f in text:
            found_facilities.append(f)
    if found_facilities:
        entities["facility"] = found_facilities

    # 2) Date extraction using predefined regex patterns
    for pat in DATE_PATTERNS:
        m = re.search(pat, text)
        if m:
            entities["date"] = [m.group(0)]
            break

    # 3) Priority extraction based on indicative keywords
    # Stops at the first matched priority level
    for level, words in PRIORITY_WORDS.items():
        for w in words:
            if w in text:
                entities["priority"] = [level]
                return entities

    return entities
