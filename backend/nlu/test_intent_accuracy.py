import json
from collections import defaultdict

try:
    from .model import NLUModel
except ImportError:
    from model import NLUModel


def evaluate_intent_accuracy():
    """评估意图识别正确率：每类前2条做few-shot，后18条做测试。"""
    nlu = NLUModel()

    samples = nlu.intent_test_samples
    if not samples:
        print("测试集为空，请检查 train.json 数据格式。")
        return

    total = 0
    correct = 0
    by_intent = defaultdict(lambda: {"total": 0, "correct": 0})

    for sample in samples:
        text = sample["text"]
        expected = sample["intent"]

        pred = nlu.predict(text)
        predicted = pred["intent"]

        total += 1
        by_intent[expected]["total"] += 1

        if predicted == expected:
            correct += 1
            by_intent[expected]["correct"] += 1

    summary = {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "by_intent": {}
    }

    for intent, stats in by_intent.items():
        intent_total = stats["total"]
        intent_correct = stats["correct"]
        summary["by_intent"][intent] = {
            "total": intent_total,
            "correct": intent_correct,
            "accuracy": round(intent_correct / intent_total, 4) if intent_total else 0.0,
        }

    print("=== NLU Intent Accuracy ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    evaluate_intent_accuracy()
