"""Record every response the app needs into app/replay.json, so the hosted copy runs without a key.

    .venv/bin/python record.py

Runs the real stack once (live Claude calls) from the seeded state. When the app cannot reach
the API, as on GitHub Pages, it plays these back and says so in the header.
"""
import json
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

import audit
from server import app

OUT = Path(__file__).parent.parent / "app" / "replay.json"


def ndjson(response):
    lines = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    return {"rows": [m["row"] for m in lines if "row" in m], "summary": next(m["summary"] for m in lines if "summary" in m)}


if __name__ == "__main__":
    audit.reset()  # record from the seeded history, not whatever a demo left behind
    c = TestClient(app)
    exceptions = c.get("/exceptions").json()
    replay = {
        "recorded": date.today().isoformat(),
        "health": c.get("/health").json(),
        "exceptions": exceptions,
        "audit": c.get("/audit").json(),
        "explain": {},
    }
    for e in exceptions:
        r = c.post("/explain", json={"exception_id": e["id"]}).json()
        replay["explain"][e["id"]] = r
        print(e["id"], r["status"], (r.get("routing") or {}).get("model", ""))
    replay["eval_retrieval"] = ndjson(c.get("/eval/retrieval"))
    replay["eval_explain"] = ndjson(c.get("/eval/explain"))
    print("retrieval", replay["eval_retrieval"]["summary"])
    print("explain", replay["eval_explain"]["summary"])
    OUT.write_text(json.dumps(replay, indent=1))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
