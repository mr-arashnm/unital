# End-to-end presentation test for the chatbot system.
# This script loads trained models, runs predefined test samples,
# prints detailed predictions, and reports basic evaluation metrics.

import torch
from chatbot import chatbot, load_models
from chatbot.config import INTENTS, SENTIMENTS

def main():
    print("\n==============================")
    print("✅ Presentation Test STARTED")
    print("==============================\n")

    # Load trained chatbot models into memory
    load_models()
    print("✅ Models loaded successfully\n")

    # Sample test sentences used for qualitative and quantitative evaluation
    test_samples = [
        "آسانسور خراب شده و خیلی ناراحتم",
        "آب قطع است لطفاً سریع رسیدگی کنید",
        "برق پارکینگ قطع شده",
        "دوربین مداربسته لابی کار نمیکنه",
        "استخر را برای فردا رزرو کن",
        "سالن را برای جمعه رزرو میخواهم",
        "باشگاه رو برای امروز میخوام",
        "زمان خالی سالن رو بهم بگو",
        "وضعیت تعمیرات آسانسور چیست؟",
        "درخواست من انجام شد؟",
        "چرا درخواست من هنوز حل نشده؟",
        "پیگیری وضعیت خدمات واحد من",
        "شارژ پرداخت شده؟",
        "بدهی من چقدر است؟",
        "مبلغ شارژ این ماه زیاد شده و ناراحتم",
        "فاکتور این ماه رو میخوام"
    ]

    # Ground-truth intent labels for evaluation
    y_true_intent = [
        "support_issue", "support_issue", "support_issue", "support_issue",
        "facility_reservation", "facility_reservation", "facility_reservation", "facility_reservation",
        "operation_status", "operation_status", "operation_status", "operation_status",
        "financial_inquiry", "financial_inquiry", "financial_inquiry", "financial_inquiry"
    ]

    # Ground-truth sentiment labels for evaluation
    y_true_sent = [
        "negative", "negative", "negative", "negative",
        "neutral", "neutral", "neutral", "neutral",
        "neutral", "neutral", "negative", "neutral",
        "neutral", "neutral", "negative", "neutral"
    ]

    preds_intent = []
    preds_sent = []

    print("✅ Predictions Table:")
    for i, text in enumerate(test_samples):
        # Run model inference for each test sample
        result = chatbot.predict(text)
        intent = result["intent"]
        sentiment = result["sentiment"]

        preds_intent.append(intent)
        preds_sent.append(sentiment)

        entities = result.get("entities", {})
        prob_intent = [round(p, 3) for p in result.get("intent_prob", [])]
        prob_sent = [round(p, 3) for p in result.get("sentiment_prob", [])]

        # Display detailed prediction output
        print(f"[{i+1}] TEXT: {text}")
        print(f"    Intent: {intent} | Sentiment: {sentiment}")
        print(f"    Entities: {entities}")
        print(f"    IntentProb: {prob_intent}")
        print(f"    SentProb:   {prob_sent}")
        print("------------------------------------------------------------")

    # Compute simple accuracy metrics
    correct_intent = sum([p == t for p, t in zip(preds_intent, y_true_intent)])
    correct_sent = sum([p == t for p, t in zip(preds_sent, y_true_sent)])
    total = len(test_samples)

    print("\n==============================")
    print("📌 Evaluation Metrics")
    print("==============================")
    print(f"✅ Intent Accuracy: {correct_intent / total * 100:.2f}%")
    print(f"✅ Sentiment Accuracy: {correct_sent / total * 100:.2f}%")

    # Utility function for computing a simple confusion matrix
    def confusion_matrix(y_true, y_pred, labels):
        matrix = [[0 for _ in labels] for _ in labels]
        label_idx = {l: i for i, l in enumerate(labels)}
        for t, p in zip(y_true, y_pred):
            matrix[label_idx[t]][label_idx[p]] += 1
        return matrix

    # Intent confusion matrix
    cm_intent = confusion_matrix(y_true_intent, preds_intent, INTENTS)
    print("\n📌 Intent Confusion Matrix:")
    print(f"{'Pred':<25}" + "".join([f"{l:<20}" for l in INTENTS]))
    for i, row in enumerate(cm_intent):
        print(f"{INTENTS[i]:<25}" + "".join([f"{c:<20}" for c in row]))

    # Sentiment confusion matrix
    cm_sent = confusion_matrix(y_true_sent, preds_sent, SENTIMENTS)
    print("\n📌 Sentiment Confusion Matrix:")
    print(f"{'Pred':<10}" + "".join([f"{l:<10}" for l in SENTIMENTS]))
    for i, row in enumerate(cm_sent):
        print(f"{SENTIMENTS[i]:<10}" + "".join([f"{c:<10}" for c in row]))

    print("\n==============================")
    print("✅ Presentation Test FINISHED")
print("==============================\n")

if name == "__main__":
    main()
