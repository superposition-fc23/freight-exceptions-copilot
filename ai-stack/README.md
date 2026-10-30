# AI stack (backup for "build an AI-native app")

Python 3.12, managed by uv. Every script runs from this folder.

| File | What it is | Try it |
|---|---|---|
| `llm.py` | `ask()`, `speak()`, `transcribe()` across Claude, GPT, Gemini, Deepgram. Model registry with ids, costs, modality | `.venv/bin/python llm.py` (smoke-tests every model with a key) |
| `router.py` | XGBoost classifier choosing a model from task, modality, cost, latency, quality, input size. Policy is in `label()` | `.venv/bin/python router.py` |
| `rag.py` | LlamaIndex + local Chroma + local embeddings. Retrieval needs no key | `.venv/bin/python rag.py index docs` then `rag.py ask "question"` |
| `agents.py` | LangGraph workflow: triage, retrieve policy, draft, rule-based guard, human review or auto-send | `.venv/bin/python agents.py "exception text"` |
| `docs/` | Three sample logistics policies. Replace with the case's files and re-index |  |

## Keys

    cp .env.example .env     # then paste keys into .env

Without keys everything still runs: retrieval is real, model steps run offline with canned output.

## Which one for the prompt

- **Answer from documents** (policies, contracts, SOPs, tariffs): `rag.py`. LlamaIndex.
- **Several steps, branching, a human in the loop**: `agents.py`. LangGraph. It calls `rag.retrieve()` as one step.
- **Cost or modality trade-offs across models**: `router.py`.

## Notes

- Deepgram: `speak()` uses Aura-2 (`aura-2-thalia-en`). `transcribe()` uses Nova-3 for recorded files.
  Flux (`flux-general-en`) is live speech-to-text over a WebSocket (`client.listen.v2.connect`), for voice agents.
- Gemini is `gemini-3.6-flash` (Google lists $1.50 / $7.50 per 1M tokens). GPT-5.6 Sol cost in `llm.py` is approximate; check before quoting.
- If imports fail or the folder moves: `./setup.sh`.

## API for the dashboard

```
.venv/bin/uvicorn server:app --reload
```

| Endpoint | Returns |
|---|---|
| `GET /exceptions` | Open exceptions, soonest deadline first, each with `time_left` and an urgency `tier` (under 1h, 1h to 6h, 6h to 24h, over 24h). Optional `?type=customs_hold` |
| `GET /exceptions/{id}` | One exception |
| `GET /eval/retrieval` | Streams the retrieval eval as NDJSON, one row per question, then recall@3, precision@3 and MRR. No model calls |
| `GET /eval/explain` | Streams the end-to-end eval: every exception through `/explain`, compared with its expected outcome and top playbook section (`evals.py`) |
| `POST /correct` `{"exception_id", "action", "verdict": "right"\|"wrong", "resolved_by"}` | Ops verdict on one suggested action, appended to `data/corrections.jsonl`; returns the updated audit |
| `GET /audit` | Wrong rate per exception type against the kill switch, labelled eval cases collected, and the latest corrections |
| `POST /audit/reset` | Demo only: drops live corrections, keeps the seeded history |
| `POST /explain` `{"exception_id": "EXC-1"}` | Up to 3 suggested actions, each with a playbook section, a quote and the portal page to act on, or an abstention naming the field in doubt. Needs `ANTHROPIC_API_KEY` |

How `/explain` decides (`explain.py`):

`explain.py` is a LangGraph pipeline, `guard -> retrieve -> draft -> check_citations`, and any node can end the run with an abstention. The response carries the `path` taken and every `guard` rule with pass or fail.

1. **Guard**, deterministic and before any model call: exception type "other" never gets a suggestion, suggestions stay off for any type whose kill switch has tripped (`audit.py`: more than 5% marked wrong by ops over at least 20 reviews, both assumed), and if the sources disagree on status (broker says hold, carrier says released) the system abstains and names the field in doubt. The later event is not treated as the winner.
2. Retrieve from the resolution playbook (`docs/playbook/`, one file per section). If the top passage scores under **0.55**, abstain. The cutoff sits between the weakest case with a playbook answer (0.59) and the HS-code case that has none (0.48); six cases is a starting point, not a calibration.
3. The XGBoost router (`router.py`) picks the model: under 1h left or a second open exception on the shipment asks for quality and gets Sonnet 5.5; everything else asks for cheap and fast and gets Haiku 5.5. The choice, its confidence and the reason come back in `routing`.
4. Claude words up to 3 actions from the passages it is given, each citing a passage number and a quote.
5. Every quote is checked word for word against its passage and the portal page comes from the passage, not the model. An action that fails the check is dropped; if none survive, abstain.

Data lives in `data/exceptions.json` with a frozen demo clock, so the screens always match the prototype.

## Replay for the hosted copy

`.venv/bin/python record.py` runs every endpoint the app uses once, live, from the seeded state and writes `app/replay.json`. When the app cannot reach the API (GitHub Pages), it plays those responses back, keeps ops verdicts in the page, and says "Replay" in the header. Re-record after changing the pipeline.
