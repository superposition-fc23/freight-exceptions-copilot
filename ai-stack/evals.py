"""Live evals behind the app's Evals tab. Each yields one row at a time so the UI can stream them.

    .venv/bin/python evals.py retrieval     # no API cost
    .venv/bin/python evals.py explain       # one Claude call per exception that clears retrieval

retrieval: questions with a known gold phrase, run against the production index (k=3).
explain:   every exception through the full /explain path, compared with the expected outcome.
"""
import json
import sys
import time

from rag_eval import EVAL as POLICY_QUESTIONS

K = 3

# Paraphrased so they cannot match the playbook on wording alone.
PLAYBOOK_QUESTIONS = [
    ("Customs wants more paperwork during an inspection, how fast do we send it?", "within one business day"),
    ("Who covers the cost when customs inspects the goods?", "Exam fees are billed to the importer of record"),
    ("What happens if the security filing is late?", "5,000 USD per filing"),
    ("Should the truck still come for containers that are stuck in customs?", "Release the trucking appointment"),
    ("The carrier bumped our boxes to a later ship, what must we do and by when?", "confirm the rebooking within the hold period"),
    ("We missed the vessel deadline, what choices do we have?", "next sailing on the same service and an alternative routing"),
    ("Half the order is on a later boat, how do we plan delivery?", "Replan downstream delivery for each part separately"),
    ("The weight on the packing list is wrong, who fixes it?", "request a corrected packing list from the supplier"),
    ("Declared value differs from the invoice, what is needed before release?", "the broker must amend the entry before release"),
    ("Does the terminal clock stop while customs inspects a container?", "does not pause demurrage unless the carrier agrees in writing"),
    ("We kept the empty box too long after unloading, what is that fee?", "Detention is charged when a container is kept outside"),
]

# Expected outcome per exception: should it suggest or abstain, and which playbook section should rank first.
GOLD = {
    "EXC-1": ("suggested", "§4.2"),
    "EXC-2": ("abstained", None),   # broker says hold, carrier says released: must not act on either
    "EXC-3": ("suggested", "§5.1"),
    "EXC-4": ("suggested", "§5.2"),
    "EXC-5": ("suggested", "§6.1"),
    "EXC-6": ("abstained", None),   # no playbook section covers a missing HS code
    "EXC-7": ("abstained", None),   # type "other" is never auto-suggested
}


def retrieval_rows():
    from rag import retrieve
    for source, (question, gold) in [("policy", q) for q in POLICY_QUESTIONS] + [("playbook", q) for q in PLAYBOOK_QUESTIONS]:
        t0 = time.perf_counter()
        hits = retrieve(question, K)
        rank = next((i + 1 for i, h in enumerate(hits) if gold in h.get_content()), None)
        yield {"set": source, "question": question, "gold": gold, "rank": rank,
               "relevant": sum(gold in h.get_content() for h in hits),
               "top": hits[0].metadata.get("file_name") if hits else None,
               "top_score": round(hits[0].score, 3) if hits else None,
               "ms": round((time.perf_counter() - t0) * 1000)}


def retrieval_summary(rows):
    n = len(rows)
    return {"n": n, "k": K,
            "recall": round(sum(r["rank"] is not None for r in rows) / n, 3),
            "precision": round(sum(r["relevant"] for r in rows) / (n * K), 3),
            "mrr": round(sum(1 / r["rank"] for r in rows if r["rank"]) / n, 3)}


def explain_rows(exceptions, minutes_left):
    from explain import explain
    for e in exceptions:
        want_status, want_section = GOLD[e["id"]]
        t0 = time.perf_counter()
        r = explain(e, minutes_left(e))
        passages = (r.get("retrieval") or {}).get("passages") or []
        top_section = passages[0]["section"] if passages else None
        checks = r.get("checks") or []
        yield {"id": e["id"], "shipment": e["shipment"], "type": e["type"],
               "expected": want_status, "got": r["status"], "status_ok": r["status"] == want_status,
               "expected_section": want_section, "top_section": top_section,
               "section_ok": None if want_section is None else bool(top_section and want_section in top_section),
               "quotes_ok": sum(c["quote_found"] for c in checks), "quotes": len(checks),
               "model": (r.get("routing") or {}).get("model"), "reason": r.get("reason"),
               "ms": round((time.perf_counter() - t0) * 1000)}


def explain_summary(rows):
    sections = [r for r in rows if r["section_ok"] is not None]
    quotes = sum(r["quotes"] for r in rows)
    should_abstain = [r for r in rows if r["expected"] == "abstained"]
    return {"n": len(rows),
            "outcome_accuracy": round(sum(r["status_ok"] for r in rows) / len(rows), 3),
            "abstention_recall": round(sum(r["got"] == "abstained" for r in should_abstain) / len(should_abstain), 3),
            "top_section_hit": round(sum(r["section_ok"] for r in sections) / len(sections), 3) if sections else None,
            "citation_pass": round(sum(r["quotes_ok"] for r in rows) / quotes, 3) if quotes else None,
            "mean_ms": round(sum(r["ms"] for r in rows) / len(rows))}


if __name__ == "__main__":
    if sys.argv[1:] == ["explain"]:
        from server import DATA, enrich
        rows = []
        for row in explain_rows(DATA["exceptions"], lambda e: enrich(e)["minutes_left"]):
            rows.append(row)
            print(json.dumps(row))
        print(json.dumps(explain_summary(rows)))
    else:
        rows = []
        for row in retrieval_rows():
            rows.append(row)
            print(f"{row['rank'] or '-':>2} {row['set']:8} {row['question']}")
        print(json.dumps(retrieval_summary(rows)))
