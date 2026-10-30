"""Multi-step agent workflow with LangGraph: a shipment-exception handler you can rename and rewire.

    triage -> retrieve policy -> draft action -> guard -> (auto_send | human_review)

Each step picks its model through router.route(). Without API keys it runs in offline mode with
canned answers, so the graph itself can be shown working. Run:
    .venv/bin/python agents.py "Container MSKU123 held for CBP exam at LA, customer asks for a 700 USD credit"
"""
import json
import re
import sys
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm import ask, has_key
from rag import retrieve
from router import route


class State(TypedDict, total=False):
    exception: str
    category: str
    confidence: float
    policy: str
    draft: str
    credit_usd: float
    decision: str
    trace: list


def call(step, prompt, system="", **route_args):
    model, _, _ = route(**route_args)
    if has_key(model):
        return model, ask(model, prompt, system=system, effort="low")
    return f"{model} (offline)", None


def triage(s: State) -> State:
    model, out = call("triage",
                      f"Exception: {s['exception']}\nReturn JSON with keys category "
                      "(delay|customs_hold|damage|rolled_booking|missing_docs|other), confidence (0-1), "
                      "credit_usd (number, 0 if none requested).",
                      system="Return only JSON.", task="classify", cost=2, latency=2, quality=1)
    if out:
        data = json.loads(re.search(r"\{.*\}", out, re.S).group())
    else:
        text = s["exception"].lower()
        cat = next((c for k, c in [("cbp", "customs_hold"), ("customs", "customs_hold"), ("damage", "damage"),
                                   ("rolled", "rolled_booking"), ("delay", "delay")] if k in text), "other")
        credit = re.search(r"(\d+)\s*usd", text)
        data = {"category": cat, "confidence": 0.9 if cat != "other" else 0.4,
                "credit_usd": float(credit.group(1)) if credit else 0}
    return {**data, "trace": [f"triage via {model}: {data}"]}


def get_policy(s: State) -> State:
    hits = retrieve(f"{s['category']} {s['exception']}", k=3)
    policy = "\n".join(h.get_content() for h in hits)
    return {"policy": policy, "trace": s["trace"] + [f"retrieved {len(hits)} policy chunks (local vector store)"]}


def draft(s: State) -> State:
    model, out = call("draft",
                      f"Exception: {s['exception']}\nPolicy:\n{s['policy']}\n"
                      "Write the next action and a 3-sentence customer message. Follow the policy exactly.",
                      task="summarize", cost=1, latency=1, quality=2)
    return {"draft": out or f"[offline draft for a {s['category']} exception]",
            "trace": s["trace"] + [f"draft via {model}"]}


def guard(s: State) -> State:
    # Deterministic rules, not a model: these are the must-not requirements.
    reasons = []
    if s.get("confidence", 0) < 0.7:
        reasons.append(f"low triage confidence {s.get('confidence')}")
    if s.get("credit_usd", 0) > 500:
        reasons.append(f"credit {s['credit_usd']} USD is above the 500 USD auto-approve limit")
    if re.search(r"\[[^\]]+\]", s.get("draft", "")) and "offline" not in s.get("draft", ""):
        reasons.append("draft has unfilled placeholders, e.g. a new ETA the system does not know")
    decision = "human_review" if reasons else "auto_send"
    return {"decision": decision, "trace": s["trace"] + [f"guard: {decision}" + (f" ({'; '.join(reasons)})" if reasons else "")]}


def human_review(s: State) -> State:
    return {"trace": s["trace"] + ["queued for an operator with draft and reasons attached"]}


def auto_send(s: State) -> State:
    return {"trace": s["trace"] + ["sent to customer, logged for audit"]}


graph = StateGraph(State)
for name, fn in [("triage", triage), ("get_policy", get_policy), ("draft", draft), ("guard", guard),
                 ("human_review", human_review), ("auto_send", auto_send)]:
    graph.add_node(name, fn)
graph.add_edge(START, "triage")
graph.add_edge("triage", "get_policy")
graph.add_edge("get_policy", "draft")
graph.add_edge("draft", "guard")
graph.add_conditional_edges("guard", lambda s: s["decision"], ["human_review", "auto_send"])
graph.add_edge("human_review", END)
graph.add_edge("auto_send", END)
app = graph.compile()


if __name__ == "__main__":
    exception = sys.argv[1] if len(sys.argv) > 1 else \
        "Container MSKU123 held for CBP exam at LA, customer asks for a 700 USD credit"
    result = app.invoke({"exception": exception})
    for line in result["trace"]:
        print("-", line)
    print("\n" + result["draft"])
    print("\nGraph (paste into mermaid.live):\n" + app.get_graph().draw_mermaid())
