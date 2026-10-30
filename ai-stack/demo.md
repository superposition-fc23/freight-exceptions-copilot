# AI stack demo sheet

Walk through this without running anything. Run a command only if she asks; the output below is what it prints.
All commands run from `ai-stack`. Real runs with Claude, captured 2026-10-21.

**The one-line architecture:** a cheap model triages, retrieval grounds the answer in policy, a strong model drafts,
and deterministic rules (not a model) decide whether a person must approve before anything reaches a customer.

```
exception text -> triage (Haiku 5.5) -> retrieve policy (local vector store) -> draft (Opus 5.5) -> guard (rules) -> auto_send | human_review
```

---

## 1. Retrieval (RAG): `rag.py`

```bash
.venv/bin/python rag.py ask "Does a customs exam pause demurrage charges?"
```

```
[1] 0.64 customs-holds.md
[2] 0.56 demurrage-policy.md
[3] 0.55 exception-sop.md

No, not by default. Time spent on a customs exam does not pause demurrage unless the carrier agrees
in writing [1]. ... charges keep running during an exam hold, which usually adds 3 to 10 days [1].
```

**When the documents don't have the answer** (`"What is the demurrage rate at Rotterdam?" --model haiku-5.5`):

```
The sources don't give a demurrage rate for Rotterdam. They only cover US West Coast ports. ...
you'd need the carrier's or terminal's Rotterdam tariff.
```

**Design notes**
- **Chunking, measured** (`rag_eval.py`, 16 paraphrased questions, k=3):

  | chunk/overlap | chunks | recall@3 | precision@3 | MRR |
  |---|---|---|---|---|
  | 256/32 | 3 | 1.00 | 0.33 | 0.97 |
  | 96/16 | 7 | 0.94 | 0.33 | 0.94 |
  | 48/8 | 27 | 0.88 | 0.29 | 0.80 |

  Read it honestly: at 256 every doc is one chunk and k=3 returns everything, so recall 1.00 is trivially true. MRR is the
  meaningful number there. Precision@3 tops out at 0.33 because each question has one right chunk. Smaller chunks lost
  recall here because rules got split from their context. On a real corpus (thousands of chunks, k much smaller than
  the corpus) I would rerun this sweep and pick the size by recall@k and MRR, not by intuition.
- **Embeddings:** `bge-small-en-v1.5`, running locally. No data leaves the machine, no per-query cost. In production: compare a hosted embedding model on our own retrieval eval before switching.
- **Vector store:** Chroma on disk for the demo. In production: pgvector next to the shipment data, or a managed store, plus metadata filters (port, carrier, customer contract) so a Rotterdam question can't pull a Los Angeles rule.
- **Grounding:** the answer prompt says "answer only from the numbered sources, cite them, say so if they don't contain the answer". The Rotterdam result is that rule working.
- **What I'd add next:** hybrid search (keyword + vector) for exact codes like HTS numbers and container IDs, a reranker, and an eval set of real ops questions with the right source marked, measuring retrieval hit rate before answer quality.

---

## 2. Model router: `router.py`

```bash
.venv/bin/python router.py
```

```
Router trained on synthetic data, held-out accuracy 94.9%

extract,   text,  cost high, latency high, quality med        -> haiku-5.5
reason,    text,  cost low,  latency low,  quality high       -> opus-5.5
extract,   image, quality high                                -> opus-5.5
summarize, text,  quality high, 800K tokens of input          -> gpt-5.6-sol
chat,      audio, latency high                                -> gemini-3.6-flash
speak                                                         -> deepgram-aura
```

**Design notes**
- **Features:** task type, modality, how much cost / latency / quality matter, input size.
- **Honest caveat:** it is trained on data generated from my own rules (`label()`), so it is a rules engine wearing an ML costume. The 94.9% only measures how well it learned my rules.
- **How it becomes real:** log production requests, label each with the cheapest model that met the quality bar (by eval or human review), retrain. That is when a learned router beats rules.
- **Before building a cascade at all:** first test the strongest model at lower effort. One model means one prompt cache and fewer failure modes; a router earns its place only when that test shows real savings.
- **Safety net:** the router skips models with no API key, and Claude calls have server-side fallback if a request is refused.

---

## 3. Agent workflow: `agents.py` (LangGraph)

```bash
.venv/bin/python agents.py "Container MSKU123 held for CBP exam at LA, customer asks for a 700 USD credit"
```

```
- triage via haiku-5.5: {'category': 'customs_hold', 'confidence': 0.97, 'credit_usd': 700}
- retrieved 3 policy chunks (local vector store)
- draft via opus-5.5
- guard: human_review (credit 700 USD is above the 500 USD auto-approve limit)
- queued for an operator with draft and reasons attached

Next Action: Escalate the 700 USD credit request to an operator. Do not issue it automatically.
- Exam fees are paid by the importer of record.
- Demurrage keeps running during the exam unless the carrier agrees in writing (4 free days at LA,
  then 150 USD/day for days 1 to 4, 300 USD/day from day 5). Notify the customer 1 day before free time ends.
- Exam adds 3 to 10 days, over 48 hours, so tell the customer the cause and new ETA within 4 business hours.
```

```bash
.venv/bin/python agents.py "Booking ABC-778 was rolled by the carrier to next week's sailing from Shanghai to Long Beach"
```

```
- triage via haiku-5.5: {'category': 'rolled_booking', 'confidence': 0.97, 'credit_usd': 0}
- retrieved 3 policy chunks (local vector store)
- draft via opus-5.5
- guard: human_review (draft has unfilled placeholders, e.g. a new ETA the system does not know)
```

**The story behind the second case (tell this one).** On the first run this case was **auto-sent** with
"[new ETA date]" still in the customer message. The model did the right thing by not inventing an ETA;
the system did the wrong thing by sending it anyway. I added a guard rule for unfilled placeholders.
The lesson: test the system, not just the model, and put the "must not" rules in code, not in the prompt.

**Design notes**
- **Why a graph instead of one big prompt:** each step has its own model, its own cost and its own test, and the guard is a branch you can see and audit.
- **Guard rules are code, not a model:** low triage confidence (under 0.7), credit over 500 USD, unfilled placeholders. These are the must-not requirements, and they are testable.
- **Cost per exception:** Haiku triage is a fraction of a cent; Opus drafting is a few cents. Measured against an operator's time on the same exception.
- **Kill switch:** one flag that forces every exception to human_review, tripped automatically if the human-override rate or customer complaints cross a threshold.
- **Memory (what I'd add):** a LangGraph checkpointer so a human-review case actually pauses and resumes after approval, and a long-term store for per-customer facts (for example, a customer who always disputes demurrage). Postgres-backed in production.

---

## 4. Calling any model: `llm.py`

```bash
.venv/bin/python llm.py
```

```
opus-5.5   ok      sonnet-5.5 ok      haiku-5.5 ok
opus-5     ok      sonnet-5   ok
gpt-5.6-sol, gemini-3.6-flash, deepgram   skipped until keys are added
```

- One `ask(model, prompt)` for every provider, each through its official SDK. Keys in `.env`.
- MCP is for giving a model tools and data, not for calling a model.

---

## Questions she might ask

| Question | Short answer |
|---|---|
| How do you know it works? | An eval set of real exceptions with the right category, policy and action marked. Triage accuracy, retrieval hit rate, and the share of drafts operators send unchanged. |
| How do you evaluate the RAG answers? | Two layers. **Retrieval:** recall@k and MRR on labeled questions (`rag_eval.py`). **Answers:** faithfulness (no contradiction or distortion of the sources), groundedness (every claim traceable to a retrieved span, even if it is true elsewhere; the stricter one here, since a rate that is right for some carrier but not in our contract still fails), answer relevancy, and abstention on out-of-scope questions. Scored with DeepEval using an LLM as judge; its built-in faithfulness metric mainly catches contradictions, so groundedness gets a custom G-Eval rubric. Define the metric by what it checks, then confirm the tool checks that. |
| Can you trust an LLM judge? | Only after checking it: humans label ~100 answers, the judge must agree on 90%+, the judge is a different or stronger model than the one being judged, and it is rechecked whenever the judge prompt or model changes. |
| What's the counter-metric? | Customer escalations and credits issued after an auto-sent message. Automation raises throughput by accepting more wrong answers unless someone watches this. |
| What breaks first in production? | Bad inputs: missing fields, wrong container IDs, policies that conflict across carriers. Then carrier data we don't control. Volume is the easy part. |
| Why not let the agent issue credits? | Money moving is irreversible and the limit is a business rule. The model drafts; a rule decides; a person approves above the threshold. |
| How would you roll it out? | Shadow mode first (drafts only, operators compare), then auto-send for one exception type with the lowest risk (rolled bookings), then widen as the override rate stays under the threshold. |
