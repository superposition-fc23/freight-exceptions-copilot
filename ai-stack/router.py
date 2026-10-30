"""Model router: an XGBoost classifier that picks a model from llm.MODELS for a request.

Features: task type, modality, cost / latency / quality priority, input size.
It trains on a synthetic set generated from the policy in label() below, so the policy is
explicit and editable during the case. In production you would retrain it on logged
requests labelled with the cheapest model that met the quality bar.

    .venv/bin/python router.py                      # train, report accuracy, show examples
    from router import route; route(task="extract", modality="text", cost=2)
"""
import random

import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from llm import MODELS, has_key

TASKS = ["classify", "extract", "summarize", "chat", "reason", "code", "speak", "listen"]
MODALITIES = ["text", "image", "audio"]
LABELS = ["haiku-5.5", "sonnet-5.5", "opus-5.5", "gpt-5.6-sol", "gemini-3.6-flash",
          "deepgram-aura", "deepgram-stt"]


def label(task, modality, cost, latency, quality, input_k):
    """The routing policy. Priorities are 0 low, 1 medium, 2 high. input_k is input size in thousands of tokens."""
    if task == "speak":
        return "deepgram-aura"
    if task == "listen" or (modality == "audio" and task != "chat"):
        return "deepgram-stt"
    if modality == "audio":
        return "gemini-3.6-flash"                     # native audio understanding in one call
    if task in ("reason", "code") and quality == 2:
        return "opus-5.5" if cost < 2 else "sonnet-5.5"
    if task in ("classify", "extract") and quality < 2:
        return "haiku-5.5"
    if cost == 2 and latency == 2:
        return "haiku-5.5" if modality == "text" else "gemini-3.6-flash"
    if quality == 2 and input_k > 500:
        return "gpt-5.6-sol"                          # second opinion / long-context alternative
    if quality == 2:
        return "opus-5.5"
    return "sonnet-5.5"


def encode(task, modality, cost, latency, quality, input_k):
    return [TASKS.index(task), MODALITIES.index(modality), cost, latency, quality, input_k]


def synth(n=4000, noise=0.03, seed=7):
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n):
        row = (rng.choice(TASKS), rng.choice(MODALITIES), rng.randint(0, 2), rng.randint(0, 2),
               rng.randint(0, 2), rng.choice([1, 10, 50, 200, 800]))
        target = label(*row)
        if rng.random() < noise:                      # a little label noise, like real logs
            target = rng.choice(LABELS)
        X.append(encode(*row))
        y.append(LABELS.index(target))
    return np.array(X), np.array(y)


def train():
    X, y = synth()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=0)
    model = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.2, eval_metric="mlogloss")
    model.fit(X_tr, y_tr)
    return model, (model.predict(X_te) == y_te).mean()


_model = None


def route(task="chat", modality="text", cost=1, latency=1, quality=1, input_k=10, require_key=True):
    """Return (model_key, confidence, ranked alternatives). Skips models with no API key if require_key."""
    global _model
    if _model is None:
        _model, _ = train()
    probs = _model.predict_proba(np.array([encode(task, modality, cost, latency, quality, input_k)]))[0]
    ranked = [(LABELS[i], float(probs[i])) for i in np.argsort(probs)[::-1]]
    usable = [r for r in ranked if not require_key or has_key(r[0])] or ranked
    return usable[0][0], usable[0][1], ranked[:3]


if __name__ == "__main__":
    model, acc = train()
    _model = model
    print(f"Router trained on synthetic data, held-out accuracy {acc:.1%}\n")
    examples = [
        dict(task="extract", modality="text", cost=2, latency=2, quality=1),
        dict(task="reason", modality="text", cost=0, latency=0, quality=2),
        dict(task="extract", modality="image", cost=1, latency=1, quality=2),
        dict(task="summarize", modality="text", cost=1, latency=1, quality=2, input_k=800),
        dict(task="chat", modality="audio", cost=1, latency=2, quality=1),
        dict(task="speak", modality="text"),
    ]
    for ex in examples:
        pick, conf, top = route(**ex, require_key=False)
        print(f"{str(ex):95} -> {pick} ({conf:.0%})")
    print(f"\nModels in registry: {', '.join(MODELS)}")
