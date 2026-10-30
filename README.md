# Freight exceptions copilot

A self-serve exceptions dashboard for a digital freight forwarder's customers, built in a timed, AI-assisted product case and then wired to a working AI stack.

The commit history is the build log: each step from blank template to working prototype is its own commit.

## The brief

Importers find out that a shipment has a problem (a customs hold, a missed vessel, a document error) late, usually in an email from their ops contact, and then wait for someone to tell them what to do. Design a self-serve experience that lets the customer see exceptions as they happen and act on them, with the forwarder's ops team as the backstop. Define testable requirements, scope a v1 with engineering, and identify the risks.

## Layout

| Folder | What |
|---|---|
| `harness/` | The blank case template and the `CLAUDE.md` working rules used to build the case in 45 minutes with Claude Code |
| `case/` | The case itself: `index.html` is the requirements report (problem, users, scope, data model, requirements, metrics, risks, phasing), `prototype.html` is the three-screen prototype |
| `app/` | The live app: the exceptions board from the prototype, backed by the API. Pick a card to see suggested actions generated on the fly, with the router's model choice, retrieval scores against the cutoff, and a check that every quote exists in its playbook passage |
| `ai-stack/` | Python 3.12: model calls (`llm.py`), an XGBoost model router (`router.py`), retrieval over the policy docs with LlamaIndex and Chroma (`rag.py`, evaluated in `rag_eval.py`), and a LangGraph agent with a deterministic guard (`agents.py`). Run `./setup.sh` once. |

## Run it

```
cd ai-stack
./setup.sh                      # once: Python env, local embedding model, vector index
cp .env.example .env            # add ANTHROPIC_API_KEY
.venv/bin/uvicorn server:app    # then open http://localhost:8000
```
