---
phase: 2
title: Run Correlation & Trace Tree
status: completed
effort: ''
---

# Phase 2: Run Correlation & Trace Tree

## Overview

Make each pipeline run a single, identifiable LangSmith trace tree that links back to its `agent_runs`
row. Pass run metadata + tags into `graph.invoke`, and decorate the non-LLM collector with `@traceable`
so it appears as a span alongside the auto-traced analyst/editor LLM calls.

## Requirements

- Functional: a run's trace carries `run_name=brief-<date>`, `metadata={run_id, brief_date, env}`, and
  `tags=[env, "pipeline"]`. The collector node shows as a span in the same tree.
- Non-functional: zero behavior change when tracing is off — `@traceable` is a transparent pass-through
  without a key/flag; the `config=` arg to `graph.invoke` is ignored by LangGraph when not tracing.

## Architecture

LangGraph forwards the `config` dict's `metadata`/`tags`/`run_name` to the LangSmith tracer. `run_id`
(the same UUID written to `agent_runs`) becomes searchable metadata, so a LangSmith trace ↔ DB row lookup
is one click either direction. `@traceable` on `collector_node` pulls the deterministic data-assembly
step into the trace tree (analyst/editor already auto-trace as LLM calls). DeepSeek's `usage_metadata`
already flows through `ChatOpenAI`, so token counts appear per-call automatically — no extra wiring.

## Related Code Files

- Modify: `backend/app/pipeline/run.py` (add `config=` to the `graph.invoke` call)
- Modify: `backend/app/pipeline/nodes_collector.py` (`@traceable` on `collector_node`)

## Implementation Steps

1. **`run.py`** — change the invoke (around line 124) to:
   ```python
   final_state = graph.invoke(
       initial_state,
       config={
           "run_name": f"brief-{target_date.isoformat()}",
           "metadata": {
               "run_id": run_id,
               "brief_date": target_date.isoformat(),
               "env": settings.LANGSMITH_ENV,
           },
           "tags": [settings.LANGSMITH_ENV, "pipeline"],
       },
   )
   ```
   `settings` is already imported in `run_pipeline`. The `config` arg is harmless when tracing is off.
2. **`nodes_collector.py`** — decorate the node:
   ```python
   from langsmith import traceable

   @traceable(run_type="chain", name="collector")
   def collector_node(state: BriefState) -> BriefState:
       ...
   ```
   Guard the import defensively only if `langsmith` is not guaranteed present — but it ships transitively
   via `langchain-core`, so a plain import is fine. Confirm `langsmith` resolves in the venv during
   implementation; if it somehow doesn't, add it to `pyproject.toml` deps rather than try/except-ing.
3. Manual verification (needs a real key, dev): run
   `uv run python -m app.pipeline.run --date 2026-06-20` with the flag on and confirm in the LangSmith UI:
   one trace named `brief-2026-06-20`, children `collector → analyst → editor`, prompts + token counts on
   the LLM spans, retry attempts visible, and `run_id` in metadata matching the new `agent_runs` row.

## Success Criteria

- [ ] Traced run produces one tree: `collector → analyst → editor`, correct `run_name`.
- [ ] Trace metadata `run_id` equals the `agent_runs.run_id` for the same run; `env` tag present.
- [ ] Analyst/editor spans show prompts, input/output, and token counts; retries appear as separate attempts.
- [ ] With tracing off, the run completes identically and `pytest` still passes (no key required).

## Risk Assessment

- **`@traceable` import coupling.** If `langsmith` were absent the import would crash the collector even
  when tracing is off. Mitigation: verify it resolves transitively; if not, pin it in `pyproject.toml`
  (cheap, one line) — preferred over a try/except that muddies the import.
- **Metadata leakage.** `run_id`/`brief_date` are non-sensitive; safe to send. No PII in metadata.
