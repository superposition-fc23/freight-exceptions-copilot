"""Suggested actions for one exception, each tied to a playbook passage (R3, N2).

    .venv/bin/python explain.py EXC-1

Retrieval decides whether we may suggest anything at all; the model only words actions
from passages we hand it. Quotes and portal pages are checked against the passage text,
so the model cannot invent a citation or a link.
"""
import json
import re
import sys
import time

from llm import ask
from rag import retrieve

# Tuned on the 6 typed exceptions in data/exceptions.json: every case with a playbook answer
# scores >= 0.59 on its top passage, the HS-code case with no playbook section scores 0.48.
# Six cases is a starting point, not a calibration; the ops corrections log is the real eval set.
CUTOFF = 0.55
FLOOR = 0.45  # passages below this are not offered to the model even when the top one clears the cutoff
MAX_ACTIONS = 3

SYSTEM = (
    "You write suggested next actions for a logistics planner looking at one shipment exception. "
    "Write each action as an instruction to the planner, who acts in the portal themselves. "
    "Use only the numbered playbook passages. Each action must cite one passage by number and include "
    "a short quote copied word for word from that passage. Do not suggest anything the passages do not "
    "support, do not invent deadlines, amounts or parties, and do not repeat the same action twice. "
    'Reply with JSON only: {"actions": [{"action": "...", "source": 1, "quote": "..."}]}, at most 3 actions, '
    "most urgent first. An empty list is a valid answer."
)


def query_for(e):
    return f"How to resolve a {e['type'].replace('_', ' ')}: {e['detail'][:200]}"


def _section(text):
    first = text.strip().splitlines()[0]
    return first.lstrip("# ").strip()


def _portal_page(text):
    m = re.search(r"Portal page:\s*(\w+)", text)
    return m.group(1) if m else None


def _norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def pick_model(e, minutes_left=None):
    """Ask the XGBoost router for a model. Urgent or compound exceptions need reasoning across
    passages, so they ask for quality; routine ones ask for cheap and fast."""
    from router import route
    urgent = minutes_left is not None and minutes_left < 60
    compound = any(t.startswith("also ") for t in e.get("tags", []))
    if urgent or compound:
        features = dict(task="reason", modality="text", cost=2, latency=1, quality=2, input_k=1)
        why = " and ".join(w for w, on in [("under 1h left", urgent), ("a second open exception on the shipment", compound)] if on)
    else:
        features = dict(task="summarize", modality="text", cost=2, latency=2, quality=1, input_k=1)
        why = "routine: one exception, time to spare"
    model, confidence, top = route(**features)
    return {"model": model, "confidence": round(confidence, 2), "reason": why, "features": features,
            "alternatives": [{"model": m, "p": round(p, 2)} for m, p in top]}


def abstain(e, reason, field, retrieval=None):
    return {"exception_id": e["id"], "status": "abstained", "reason": reason, "field_in_doubt": field,
            "actions": [], "retrieval": retrieval}


def explain(e, minutes_left=None):
    if e["type"] == "other":
        return abstain(e, 'Exception type "other" is never auto-suggested', "exception type")

    t0 = time.perf_counter()
    hits = [h for h in retrieve(query_for(e), 10) if "/playbook/" in h.metadata.get("file_path", "")]
    passages = [{"n": i + 1, "section": _section(h.get_content()), "score": round(h.score, 3),
                 "portal_page": _portal_page(h.get_content()), "text": h.get_content()}
                for i, h in enumerate(h for h in hits[:4] if h.score >= FLOOR)]
    retrieval = {"top_score": round(hits[0].score, 3) if hits else None, "cutoff": CUTOFF,
                 "query": query_for(e), "ms": round((time.perf_counter() - t0) * 1000),
                 "passages": [{k: p[k] for k in ("section", "score")} for p in passages]}
    if not hits or hits[0].score < CUTOFF:
        return abstain(e, "Retrieval below confidence cutoff", "action", retrieval)

    context = "\n\n".join(f"[{p['n']}] {p['text']}" for p in passages)
    prompt = (f"Exception: {e['type'].replace('_', ' ')} on {e['shipment']}, {e['containers']['affected']} of "
              f"{e['containers']['total']} containers. {e['detail']}. Deadline: {e['deadline_reason']}.\n\n"
              f"Playbook passages:\n{context}")
    routing = pick_model(e, minutes_left)
    t1 = time.perf_counter()
    raw = ask(routing["model"], prompt, system=SYSTEM, max_tokens=1500, effort="low")
    routing["ms"] = round((time.perf_counter() - t1) * 1000)
    try:
        proposed = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])["actions"]
    except (ValueError, KeyError):
        return {**abstain(e, "Model reply was not valid JSON", "action", retrieval), "routing": routing}

    by_n = {p["n"]: p for p in passages}
    actions, dropped, checks = [], 0, []
    for a in proposed:
        p = by_n.get(a.get("source"))
        # N2: no suggestion without a passage that really contains the quoted words.
        ok = bool(p and a.get("quote") and _norm(a["quote"]) in _norm(p["text"]))
        checks.append({"action": a.get("action"), "source": a.get("source"), "quote_found": ok})
        if not ok:
            dropped += 1
            continue
        actions.append({"action": a["action"], "citation": {"section": p["section"], "quote": a["quote"]},
                        "portal_page": p["portal_page"]})
    if not actions:
        return {**abstain(e, "No suggested action could be tied to a playbook passage", "action", retrieval),
                "routing": routing}
    return {"exception_id": e["id"], "status": "suggested", "actions": actions[:MAX_ACTIONS],
            "dropped_uncited": dropped, "checks": checks, "routing": routing, "retrieval": retrieval}


if __name__ == "__main__":
    data = json.load(open("data/exceptions.json"))["exceptions"]
    ids = sys.argv[1:] or [e["id"] for e in data]
    for e in (e for e in data if e["id"] in ids):
        print(json.dumps(explain(e), indent=2))
