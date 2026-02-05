# chatbot/data_generator.py
# Synthetic dataset generator for training the chatbot.
# This module creates labeled text samples for intent classification,
# sentiment analysis, and entity extraction using predefined templates.

import random

# Intent-specific text templates.
# Each intent maps to a list of natural language patterns
# used to generate synthetic user messages.
INTENT_TEMPLATES = {
    "support_issue": [
        "{facility} خراب شده و خیلی ناراحتم",
        "{facility} درست کار نمی‌کنه، لطفاً رسیدگی کنید",
        "مشکل فنی در {facility} دارم، فوری پیگیری کنید",
        "میخوام گزارش خرابی {facility} ثبت کنم"
    ],
    "facility_reservation": [
        "{facility} را برای {date} رزرو کن",
        "میخوام {facility} رو برای {date} رزرو کنم",
        "زمان خالی {facility} رو بهم بگو",
        "رزرو {facility} تایید شد؟"
    ],
    "operation_status": [
        "وضعیت {facility} چیست؟",
        "درخواست من در مورد {facility} حل شد؟",
        "کار من در {facility} کی انجام میشه؟",
        "پیگیری وضعیت {facility}"
    ],
    "financial_inquiry": [
        "شارژ {facility} پرداخت شده؟",
        "بدهی من چقدر است؟",
        "مبلغ شارژ {facility} این ماه چقدره",
        "چرا شارژ زیاد شده؟",
        "فاکتور این ماه رو میخوام"
    ]
}

# Sample entities used to populate templates.
# These lists simulate real-world facilities, dates, and priorities.
FACILITIES = ["آسانسور", "برق", "دوربین", "سالن", "استخر", "باشگاه", "لابی", "پارکینگ", "روف گاردن"]
DATES = ["امروز", "فردا", "جمعه", "شنبه", "یکشنبه"]
PRIORITIES = ["low", "medium", "high"]

# Supported sentiment labels for sentiment classification
SENTIMENTS = ["positive", "neutral", "negative"]

def generate_dataset(total_per_intent=500, seed=42):
    """
    Generate a synthetic dataset for chatbot training.

    Each sample consists of:
    - Generated text
    - Intent label
    - Sentiment label
    - Extracted entities dictionary
    """
    random.seed(seed)
    dataset = []

    # Iterate over each intent and its corresponding templates
    for intent, templates in INTENT_TEMPLATES.items():
        for _ in range(total_per_intent):
            template = random.choice(templates)
            text = template

            # Replace entity placeholders with randomly selected values
            if "{facility}" in text:
                facilities_used = random.sample(FACILITIES, k=random.randint(1, 2))
                text = text.replace("{facility}", " و ".join(facilities_used))
            if "{date}" in text:
                text = text.replace("{date}", random.choice(DATES))

            # Assign sentiment using intent-specific probability distributions
            if intent == "support_issue":
                sentiment = random.choices(SENTIMENTS, weights=[0.1, 0.3, 0.6])[0]
            elif intent == "facility_reservation":
                sentiment = random.choices(SENTIMENTS, weights=[0.2, 0.5, 0.3])[0]
            elif intent == "operation_status":
                sentiment = random.choices(SENTIMENTS, weights=[0.1, 0.7, 0.2])[0]
            elif intent == "financial_inquiry":
                sentiment = random.choices(SENTIMENTS, weights=[0.05, 0.6, 0.35])[0]
            else:
                sentiment = "neutral"

            # Build entity annotations based on the intent type
            entities = {}
            if intent == "support_issue":
                entities["facility"] = facilities_used
                # Optionally assign a priority level to support requests
                if random.random() < 0.3:
                    entities["priority"] = [random.choice(PRIORITIES)]
            elif intent == "facility_reservation":
                entities["facility"] = facilities_used
                if "{date}" in template:
                    entities["date"] = [random.choice(DATES)]
            elif intent == "operation_status":
                entities["facility"] = facilities_used
            elif intent == "financial_inquiry":
                entities["facility"] = facilities_used
            # Append the generated sample as a tuple
            dataset.append((text, intent, sentiment, entities))

    # Shuffle dataset to avoid ordering bias during training
    random.shuffle(dataset)
    return dataset
