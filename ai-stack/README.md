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

Data lives in `data/exceptions.json` with a frozen demo clock, so the screens always match the prototype.
