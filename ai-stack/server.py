# API behind the exceptions dashboard. Run: .venv/bin/uvicorn server:app --reload
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DATA = json.loads((Path(__file__).parent / "data" / "exceptions.json").read_text())
NOW = datetime.fromisoformat(DATA["demo_now"])  # frozen clock so the demo always looks the same

app = FastAPI(title="Freight exceptions API")
# The prototype opens from the filesystem or GitHub Pages, so allow any origin; there is no auth or write path to protect yet.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def tier(minutes_left):
    """Colour is the clock (R7): under 1h, 1h to 6h, 6h to 24h, over 24h. No deadline is never green."""
    if minutes_left is None:
        return "unknown"
    if minutes_left < 60:
        return "under_1h"
    if minutes_left < 6 * 60:
        return "1h_to_6h"
    if minutes_left < 24 * 60:
        return "6h_to_24h"
    return "over_24h"


def time_left(minutes):
    if minutes is None:
        return "deadline unknown"
    d, rem = divmod(minutes, 24 * 60)
    h, m = divmod(rem, 60)
    if d:
        return f"{d}d {h}h left" if h else f"{d}d left"
    if h:
        return f"{h}h {m}m left" if m else f"{h}h left"
    return f"{m}m left"


def enrich(e):
    deadline = datetime.fromisoformat(e["deadline"]) if e.get("deadline") else None
    minutes = max(0, int((deadline - NOW).total_seconds() // 60)) if deadline else None
    return {**e, "minutes_left": minutes, "time_left": time_left(minutes), "tier": tier(minutes)}


ROOT = Path(__file__).parent.parent
app.mount("/app", StaticFiles(directory=ROOT / "app", html=True), name="app")
app.mount("/case", StaticFiles(directory=ROOT / "case", html=True), name="case")


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/app/")


@app.get("/health")
def health():
    return {"ok": True, "now": NOW.isoformat()}


@app.get("/exceptions")
def exceptions(type: str | None = None):
    """Open exceptions, soonest deadline first; a card with no deadline sorts last."""
    rows = [enrich(e) for e in DATA["exceptions"] if type is None or e["type"] == type]
    return sorted(rows, key=lambda r: (r["minutes_left"] is None, r["minutes_left"] or 0))


def find(exception_id):
    for e in DATA["exceptions"]:
        if e["id"] == exception_id:
            return e
    raise HTTPException(404, f"No exception {exception_id}")


@app.get("/exceptions/{exception_id}")
def exception(exception_id: str):
    return enrich(find(exception_id))


class ExplainRequest(BaseModel):
    exception_id: str


@app.post("/explain")
def explain_exception(req: ExplainRequest):
    """Up to 3 cited suggested actions, or an abstention naming the field in doubt (R3, R4, N2)."""
    from explain import explain  # imported lazily so /exceptions works without the vector store loaded
    return explain(find(req.exception_id), enrich(find(req.exception_id))["minutes_left"])


def _stream(rows, summarize):
    """NDJSON: one line per eval row as it finishes, then a summary line, so the UI fills in live."""
    done = []
    for row in rows:
        done.append(row)
        yield json.dumps({"row": row}) + "\n"
    yield json.dumps({"summary": summarize(done)}) + "\n"


@app.get("/eval/retrieval")
def eval_retrieval():
    from evals import retrieval_rows, retrieval_summary
    return StreamingResponse(_stream(retrieval_rows(), retrieval_summary), media_type="application/x-ndjson")


@app.get("/eval/explain")
def eval_explain():
    from evals import explain_rows, explain_summary
    rows = explain_rows(DATA["exceptions"], lambda e: enrich(e)["minutes_left"])
    return StreamingResponse(_stream(rows, explain_summary), media_type="application/x-ndjson")
