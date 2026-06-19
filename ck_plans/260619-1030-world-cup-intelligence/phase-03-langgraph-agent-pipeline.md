---
phase: 3
title: "LangGraph Agent Pipeline"
status: done (code complete; live run needs DEEPSEEK_API_KEY)
priority: P1
effort: "2-3d"
dependencies: [2]
---

# Phase 3: LangGraph Agent Pipeline

## Overview
Wire the 3-node LangGraph StateGraph (Collector → Analyst → Editor) that turns the tournament's data-to-date into a persisted markdown brief, with run logging.

## Requirements
- Functional: a manual trigger for a date produces one `articles` row (title, summary, body_md) and one `agent_runs` log.
- Non-functional: LLM narrates only (no arithmetic); deterministic facts injected from Phase 2; per-node timing/token/cost captured.

## Architecture
- Typed shared state (TypedDict): `brief_date`, `matches`, `standings`, `computed_facts`, `intelligence` (JSON), `article`.
- **Collector node** (no LLM): calls Phase 2 collector + `standings_math`; fills `computed_facts` with **full tournament-to-date** facts (all completed results, upcoming fixtures, current table, position deltas, qualification status). <!-- Updated: Validation Session 1 - coverage = full tournament-to-date -->
- **Analyst node** (DeepSeek `deepseek-chat`/V3): input = `computed_facts` only → structured `intelligence` JSON (storylines, surprise teams, underperformers, power ranking, qualification narrative) over the whole tournament so far. Prompt forbids recomputing numbers; it cites the facts given. Reasoner (R1) deferred to V2. <!-- Updated: Validation Session 1 - model = deepseek-chat -->
- Note: full-to-date facts grow as the tournament progresses — keep prompt input bounded (summarize older matchdays, detail the latest) to control token cost.
- **Editor node** (DeepSeek): `intelligence` → markdown `article` + title + summary.
- DeepSeek via `langchain-openai` `ChatOpenAI(base_url="https://api.deepseek.com", model="deepseek-chat")`.
- Graph: linear `START → collector → analyst → editor → END`.
- Persist `article` (upsert by `brief_date`), setting `status='published'` **only after the Editor node succeeds** (keep-last-good: failed runs never publish — see Phase 5); write `agent_runs` (node timings, tokens, cost, status/error).
- Manual trigger CLI: `python -m app.pipeline.run --date YYYY-MM-DD`.

## Related Code Files
- Create: `backend/app/pipeline/state.py`, `backend/app/pipeline/graph.py`, `backend/app/pipeline/nodes_collector.py`, `backend/app/pipeline/nodes_analyst.py`, `backend/app/pipeline/nodes_editor.py`, `backend/app/pipeline/prompts.py`, `backend/app/pipeline/run.py`, `backend/app/llm/deepseek.py`
- Modify: `backend/app/data/repository.py` (article + agent_runs writes), `backend/app/config.py` (DeepSeek key)

## Implementation Steps
1. `state.py`: TypedDict state schema.
2. `deepseek.py`: ChatOpenAI client factory (base_url + key + structured-output for Analyst).
3. `nodes_collector.py`: assemble `computed_facts` from Phase 2.
4. `prompts.py` + `nodes_analyst.py`: structured-JSON intelligence; explicit "do not compute numbers, only narrate provided facts".
5. `nodes_editor.py`: markdown article + title + summary.
6. `graph.py`: build StateGraph; `run.py` CLI + persistence + `agent_runs` logging.

## Success Criteria
- [ ] `python -m app.pipeline.run --date <d>` writes one `articles` row end-to-end.
- [ ] `agent_runs` row records per-node timings, tokens, cost, status.
- [ ] Re-run same date upserts (no duplicate article).
- [ ] Spot-check: numbers in article match `computed_facts` exactly (no hallucinated math).

## Risk Assessment
- LLM drifts into recomputing standings → constrain via prompt + only pass narrated facts; spot-check in success criteria.
- DeepSeek structured-output reliability → use JSON mode / pydantic parsing with retry.
- Cost creep → 2 calls/day; log cost in `agent_runs` to confirm pennies.
