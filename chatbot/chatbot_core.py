# Core logic of the chatbot:
# - Text normalization
# - Rule-based entity extraction
# - Intent & sentiment handling
# - Response generation
# - Model loading and inference

import torch
import re
from pathlib import Path

from .model import ChatbotModel
from .tokenizer import Tokenizer
from .config import DEVICE, MODEL_PATH, MAX_LEN, INTENTS, SENTIMENTS


# -----------------------------
# 1) Text Normalization Utilities
# -----------------------------
def normalize_fa(text: str) -> str:
    """
    Normalize Persian text by:
    - Stripping leading/trailing spaces
    - Unifying Arabic/Persian characters
    - Collapsing multiple spaces
    """
    if not text:
        return ""
    text = text.strip()
    # Unify Arabic and Persian characters
    text = text.replace("ي", "ی").replace("ك", "ک")
    # Remove extra whitespaces
    text = re.sub(r"\s+", " ", text)
    return text


# -----------------------------
# 2) Simple Rule-Based Entity Extractor (Regex / Keyword)
# -----------------------------
FACILITIES = [
    "آسانسور", "برق", "آب", "گاز",
    "پارکینگ", "درب", "در", "دوربین",
    "لابی", "استخر", "سالن", "باشگاه",
    "روف", "روف گاردن", "حیاط", "تاسیسات"
]

DATE_WORDS = [
    "امروز", "فردا", "پس فردا",
    "جمعه", "شنبه", "یکشنبه",
    "دوشنبه", "سه شنبه", "چهارشنبه", "پنجشنبه"
]

PRIORITY_HIGH = ["سریع", "فوری", "اضطراری", "زود", "همین الان"]


def extract_entities(text: str) -> dict:
    """
    Extract basic entities (facility, date, priority)
    using keyword matching on normalized text.
    """
    text_n = normalize_fa(text)
    ents = {}

    # Facility extraction
    fac = []
    for f in FACILITIES:
        if f in text_n:
            fac.append(f)
    if fac:
        ents["facility"] = list(dict.fromkeys(fac))

    # Date extraction
    dates = []
    for d in DATE_WORDS:
        if d in text_n:
            dates.append(d)
    if dates:
        ents["date"] = list(dict.fromkeys(dates))

    # Priority detection (binary: high)
    pri = []
    for p in PRIORITY_HIGH:
        if p in text_n:
            pri.append("high")
            break
    if pri:
        ents["priority"] = pri

    return ents


# -----------------------------
# 3) Rule-Based Response Generator
# -----------------------------
GREETINGS = [
    "سلام", "سلامم", "درود", "وقت بخیر",
    "صبح بخیر", "عصر بخیر", "شب بخیر",
    "خسته نباشید", "hi", "hello"
]

THANKS = [
    "ممنون", "مرسی", "دمت گرم", "سپاس"
]


def is_greeting(text: str) -> bool:
    """Check whether input text is a greeting."""
    t = normalize_fa(text).lower()
    return any(g in t for g in GREETINGS)


def is_thanks(text: str) -> bool:
    """Check whether input text expresses gratitude."""
    t = normalize_fa(text).lower()
    return any(w in t for w in THANKS)


def generate_response(intent: str, sentiment: str, entities: dict, text: str) -> str:
    """
    Generate a professional, user-friendly response
    based on intent, sentiment, and extracted entities.
    """
    # Greeting / Thanks take priority over model prediction
    if is_greeting(text):
        return "سلام 😊 من پشتیبان هوشمند سیستم مجتمع هستم. مشکل یا درخواستت رو بگو تا سریع راهنماییت کنم."

    if is_thanks(text):
        return "خواهش می‌کنم 🌿 اگر باز هم کاری داشتی در خدمتم."

    # Support issue handling
    if intent == "support_issue":
        fac = ", ".join(entities.get("facility", [])) if entities.get("facility") else "مشکل اعلام‌شده"
        if sentiment == "negative":
            return f"متوجه ناراحتی شما هستم 🙏 گزارش خرابی مربوط به **{fac}** ثبت شد و برای تیم اجرایی ارسال می‌شود."
        return f"✅ گزارش مربوط به **{fac}** ثبت شد. در اولین فرصت پیگیری می‌شود."

    # Facility reservation handling
    if intent == "facility_reservation":
        fac = ", ".join(entities.get("facility", [])) if entities.get("facility") else "امکانات"
        date = ", ".join(entities.get("date", [])) if entities.get("date") else "زمان موردنظر"
        return f"✅ درخواست رزرو **{fac}** برای **{date}** ثبت شد. اگر زمان دقیق هم بفرمایید کامل‌تر می‌شود."

    # Financial inquiries
    if intent == "financial_inquiry":
        if sentiment == "negative":
            return "متوجه نگرانی شما هستم 🙏 لطفاً بفرمایید درباره **شارژ، بدهی یا پرداخت** کدام مورد سوال دارید؟"
        return "برای بررسی وضعیت مالی، لطفاً مشخص کنید: **شارژ این ماه / بدهی / تایید پرداخت**؟"

    # Operation / request status
    if intent == "operation_status":
        if sentiment == "negative":
            return "حق دارید پیگیری کنید 🙏 لطفاً شماره درخواست یا توضیح کوتاه بدهید تا وضعیتش را دقیق بررسی کنم."
        return "لطفاً بفرمایید مربوط به **کدام درخواست/خرابی** است تا وضعیت آن را اعلام کنم."

    # Fallback response
    return "متوجه نشدم 😅 لطفاً واضح‌تر بفرمایید مشکل خرابی است یا رزرو یا مالی؟"


# -----------------------------
# 4) Main Chatbot Interface Class
# -----------------------------
class Chatbot:
    """
    High-level chatbot interface:
    - Loads trained model and tokenizer
    - Runs inference
    - Produces structured prediction results
    """
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.max_len = MAX_LEN

    def load_models(self):
        """
        Load trained model checkpoint and tokenizer vocabulary.
        """
        model_path = Path(MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(f"⚠️ Model file not found at {MODEL_PATH}. Train first.")

        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)

        self.model = ChatbotModel(vocab_size=len(checkpoint["vocab"])).to(DEVICE)
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.eval()

        self.tokenizer = Tokenizer()
        self.tokenizer.word2idx = checkpoint["vocab"]
        self.max_len = checkpoint.get("max_len", MAX_LEN)

        print("✅ Models loaded successfully")

    def predict(self, text: str) -> dict:
        """
        Run inference on input text and return:
        - intent
        - sentiment
        - probabilities
        - extracted entities
        - generated response
        """
        text = normalize_fa(text)

        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Models not loaded. Please run load_models() first.")

        # Handle greeting explicitly to avoid misclassification
        if is_greeting(text):
            return {
                "intent": "greeting",
                "sentiment": "neutral",
                "intent_prob": [1.0, 0.0, 0.0, 0.0],
                "sentiment_prob": [0.0, 1.0, 0.0],
                "entities": {},
                "response_text": generate_response("greeting", "neutral", {}, text)
            }

        x = torch.tensor(
            [self.tokenizer.encode(text, self.max_len)],
            dtype=torch.long
        ).to(DEVICE)

        with torch.no_grad():
            intent_logits, sent_logits, _ = self.model(x)

        intent_prob = torch.softmax(intent_logits, dim=1)[0].cpu().tolist()
        sent_prob = torch.softmax(sent_logits, dim=1)[0].cpu().tolist()

        intent_idx = int(torch.argmax(intent_logits, dim=1).item())
        sent_idx = int(torch.argmax(sent_logits, dim=1).item())

        intent = INTENTS[intent_idx]
        sentiment = SENTIMENTS[sent_idx]

        entities = extract_entities(text)
        response_text = generate_response(intent, sentiment, entities, text)

        return {
            "intent": intent,
            "sentiment": sentiment,
            "intent_prob": intent_prob,
            "sentiment_prob": sent_prob,
            "entities": entities,
            "response_text": response_text
        }


# Ready-to-use singleton instance
chatbot = Chatbot()


def load_models():
    """Convenience wrapper for loading models globally."""
    chatbot.load_models()
