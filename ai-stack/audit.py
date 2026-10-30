"""Ops corrections, the audit trail and the kill switch (R6, N3).

Every suggested action ops reviews is logged as right or wrong, with what actually resolved
the exception. The wrong rate per exception type drives the kill switch: above THRESHOLD over
at least MIN_REVIEWED reviews, suggestions for that type stop and its cards route to ops.
Wrong verdicts with a recorded resolution are the labelled cases for the next eval set.
"""
import json
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).parent / "data"
SEED = DATA / "corrections_seed.jsonl"   # illustrative review history before the demo clock
LOG = DATA / "corrections.jsonl"         # written by POST /correct, gitignored

THRESHOLD = 0.05    # assumed
MIN_REVIEWED = 20   # assumed: below this the rate is noise, so the switch cannot trip
TYPES = ["customs_hold", "missed_vessel", "document_error"]


def _read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def corrections():
    return _read(SEED) + _read(LOG)


def record(exception, action, verdict, resolved_by="", reviewer="ops", now=None):
    if verdict not in ("right", "wrong"):
        raise ValueError("verdict must be 'right' or 'wrong'")
    row = {"at": (now or datetime.now()).isoformat(timespec="seconds"), "exception_id": exception["id"],
           "shipment": exception["shipment"], "type": exception["type"], "action": action,
           "verdict": verdict, "resolved_by": resolved_by.strip(), "reviewer": reviewer}
    with LOG.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def reset():
    LOG.unlink(missing_ok=True)


def summary():
    rows = corrections()
    by_type = []
    for t in TYPES:
        mine = [r for r in rows if r["type"] == t]
        wrong = sum(r["verdict"] == "wrong" for r in mine)
        rate = wrong / len(mine) if mine else 0.0
        by_type.append({"type": t, "reviewed": len(mine), "wrong": wrong, "wrong_rate": round(rate, 4),
                        "killed": len(mine) >= MIN_REVIEWED and rate > THRESHOLD})
    return {"threshold": THRESHOLD, "min_reviewed": MIN_REVIEWED, "by_type": by_type,
            "eval_cases": sum(r["verdict"] == "wrong" and bool(r["resolved_by"]) for r in rows),
            "trail": rows[-12:][::-1], "live_reviews": len(_read(LOG))}


def killed(exception_type):
    return next((t for t in summary()["by_type"] if t["type"] == exception_type and t["killed"]), None)
