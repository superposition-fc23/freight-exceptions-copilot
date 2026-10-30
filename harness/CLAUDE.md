# Case harness

A single-file case artifact for a timed, live product case. `index.html` is the scaffold. Fill it in place.

Build whatever the prompt asks for, step by step, including agents, retrieval, model routing or a backend. Working code goes in the `ai-stack` subfolder (Python 3.12: `llm.py` model calls, `router.py` XGBoost model router, `rag.py` LlamaIndex + Chroma, `agents.py` LangGraph; see its README; run scripts as `.venv/bin/python <file>` from inside `ai-stack`), not next to `index.html`. The rules below are about the artifact file only.

## The rules of this folder

1. **Two files.** The report lives in `index.html`; the prototype lives in `prototype.html`, full width for screen share. Both open from the filesystem. Tailwind (Play CDN, pinned 3.4.17) is already loaded; add no other frameworks or CDN links.
   - **Use Tailwind utilities for any new or reworked UI**, with the theme colors so it matches the existing styles and dark mode: `bg-surface`, `bg-surface-2`, `text-fg`, `text-fg-2`, `text-fg-3`, `border-rule`, `bg-accent`, `bg-accent-soft`, `text-ok`/`bg-ok-soft`, `text-warn`/`bg-warn-soft`, `text-stop`/`bg-stop-soft`, `font-mono`. Not raw Tailwind colors like `bg-blue-500`.
   - Preflight is off on purpose so the existing CSS stays intact; do not turn it on. Do not use `dark:` variants; the theme colors already switch.
2. **Edit, never regenerate.** Replace placeholder text in place. Keep the CSS, the section IDs and the tab script untouched unless asked. Before a new case, `./reset.sh` restores both blank templates.
3. **Placeholders are uppercase.** `TITLE`, `PROBLEM SENTENCE`, `ENTITY A`, `REF-1001`. Anything still uppercase at the end is unfinished.
4. **Never invent a number and present it as real.** Illustrative figures on the mock screens are fine and are already labelled as such. A figure anywhere else needs a source or an "assumed" marker.
5. **No em dashes anywhere.** Commas, colons, semicolons or periods.
6. **Delete unused sections** rather than leaving them empty. An empty section reads as unfinished; a missing one reads as scoped out.

## Fill order, which is also the presentation order

Work top down. Sections 01 to 03 first, because they are the scope agreement. Then 04 the model, then 05 the prototype, then 06 to 09.

If time runs short, the sections that must exist are **01 problem, 03 goal and non-goals, 05 prototype, 06 requirements**. Risks and phasing can be spoken.

## Section notes

**01 Problem.** One sentence in the user's position with no mechanism in it. Then one sentence on what it costs today.

**02 User and decision.** Who, what decision, what they do instead today. Two rows is enough.

**03 Goal and non-goals.** Three non-goals, each with half a line of reason. The assumptions note underneath is not optional: it is what invites the engineer to correct you early rather than late.

**04 The model.** Edit the SVG labels, keep the shape. Two rows: entities across the top with their cardinality, state flow underneath with one exception branch. The caption must name the trap the picture makes obvious, for example that events land on several grains while the user wants one timeline, or that the join key changes over the lifecycle.

**05 Prototype.** Build it in `prototype.html`, inside its `<main>`, and set its `<h1>`. The report's section 05 only links to it; add one line per screen there once built. Default to three screens behind tabs (`.tabs` > `button.tab[data-screen]`, each screen a `div.screen` with an id, the first with class `on`; the tab script at the bottom already handles switching):
- **Screen 1, normal.** The case that should never need a person.
- **Screen 2, uncertain.** The system declining to act and naming the field it is unsure about. This is the screen that decides whether the product is safe, and it is the one most candidates never build.
- **Screen 3, correction and audit.** The most used path in this kind of product and usually the least designed. Also where the training signal comes from.

The stylesheet already defines a list plus detail plus action shell you can reuse (`.mock`, `.mock-bar`, `.mock-top`, `.mock-body`, `.side`, `.main`, `.panel`, `table.grid`, `.pill`, `.banner`, `.conf`, `.trail`); it fits shipment queues, invoice audit queues, exception queues, quote lists and document review. Use Tailwind for anything else. Follow the user's lead if they want different screens.

**Building it in parallel.** When the user asks for the prototype to be built in parallel or in the background, launch a background agent so the conversation can continue on requirements. Give it a self-contained brief: read `index.html` sections 01 to 04 and `CLAUDE.md` section 05, edit only `prototype.html`, use only data the report states or mark fields assumed, and report back the three screen names. Do not edit `prototype.html` from the main conversation while that agent runs. When it finishes, add the one-line screen summaries to section 05 of `index.html`.

**06 Requirements.** Grammar: *When [condition], the system must [observable behaviour]. Test: [method and data].* The must-not table is where risk awareness becomes visible on the page. N3, the kill switch with a defined trigger, is the single most credible control to include.

**07 Metrics.** Always three: leading, lagging, counter. The counter metric is the one that proves seniority, because automation improves throughput by accepting more wrong answers unless somebody watches it.

**08 Risks.** Each row needs a mitigation or an owner, not a worry. The "where this plan is weak" note is said out loud, not just written.

**09 Phasing.** De-risking sequence. P1 is the smallest build that tests the riskiest assumption.

## The clock, 45 minutes

| Minutes | What |
|---|---|
| 0 to 4 | Read twice. Three clarifying questions. State the user, the decision and the scope you are taking |
| 4 to 8 | Fill 01, 02, 03 while talking. The scope agreement happens here |
| 8 to 30 | Build. Launch the prototype in the background once 01 to 03 are agreed, then requirements and model while it builds. Narrate every prompt |
| 30 to 38 | Walk the artifact in 90 seconds, then turn it into a scoping conversation with the engineer |
| 38 to 45 | The close, below |

**The clock is the thing that fails, not the content.** At minute 30 stop building regardless of state, then say **three ways this is wrong** before the walkthrough. Volunteering the weaknesses before they are found is the most senior-reading move available.

## The three clarifying questions

1. Who is the user here: the customer, the internal operator, or the customer's own system? **Default hypothesis: the customer, self-serve, with internal ops as the backstop for what the system abstains on.** Set this to the company's product direction before each case (here: customer self-serve), state it as the assumption and let the interviewer correct it. Even for an ops-flavoured prompt, ask whether the customer could resolve it themselves first. Self-serve metrics to reach for: share resolved without contacting support, tickets per 1,000 orders, time to resolution.
2. What exists today? Am I extending something or starting from nothing?
3. What does failure cost here, money or trust?

Then commit out loud: "I am solving it for this user, for this decision, and leaving out these two things. Tell me if that is the wrong cut."

## Narration rules while building

- **Say the prompt before sending it.** A good prompt names the task, the context, the output shape, and what to avoid. The "what to avoid" clause is the one that signals experience.
- **Audit output on camera.** Reject something out loud with a reason. Catching one hallucination is worth more than three extra screens.
- **Hand-write the acceptance criteria and the metric definitions yourself**, and say why: the scaffolding is commodity and the criteria are the judgement being assessed.
- **One bad prompt, then diagnose.** Fix or work around, say which you chose, move on. Never debug silently for four minutes.

## Four sentences for the engineer

- "My assumption is we are extending X rather than building new. Correct me."
- "What would change your estimate here by an order of magnitude?"
- "I am deliberately not handling Y in v1. Does that save you real work, or is the abstraction the same either way?"
- "Where does this break first in production, and is it volume, a bad input, or a system we do not control?"

**Change something in the artifact because of what they said, while they watch, and say that is what you are doing.**

## The close

Three things, in order, every time:

1. What I would cut with half the time, and what it would cost.
2. What I would want to know before anyone builds this.
3. How I would know in 90 days whether it worked, including the counter-metric.

## Do not

- Write a requirement containing "accurate", "fast" or "intuitive" without a number and a test.
- Draw a data field on a screen without either labelling it assumed or saying out loud that it is.
- Go silent while building.
