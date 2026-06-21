# LangSmith Agent Observability — Implementation

**Date**: 2026-06-22 06:43
**Severity**: Low (feature complete, code-side acceptance criteria met)
**Component**: Backend (FastAPI + LangGraph pipeline)
**Status**: Resolved (code) — manual LangSmith UI setup pending user

## What Happened

Added env-gated LangSmith tracing + monitoring over the LangGraph brief pipeline (`Collector → Analyst →
Editor`, DeepSeek via `langchain-openai`). Brainstorm → plan → cook flow. Chose Approach B: env-var
tracing + a small `observability.py` bootstrap mirroring `configure_logging()` + `@traceable` glue.

**Phase 1 (config + bootstrap):** 5 `LANGSMITH_*` settings in `config.py` (default-off). New
`observability.py::configure_tracing()` — idempotent, env-gated (flag AND key required), never raises,
atomic env-write (build dict → `os.environ.update`). Wired beside `configure_logging()` in `main.py`,
`run.py` (×2), `scheduler_entry.py`. 5 unit tests cover off/on/idempotent/never-raise.

**Phase 2 (correlation + trace tree):** `@traceable(run_type="chain", name="collector")` on
`collector_node`; `config={run_name, metadata{run_id,brief_date,env}, tags}` on `graph.invoke`. `run_id`
is the same UUID written to `agent_runs`, so trace ↔ DB row is a one-click lookup. Analyst/editor
auto-trace as LLM calls; DeepSeek `usage_metadata` already flows token counts per call.

**Phase 3 (deploy + docs):** `LANGSMITH_*` passthrough in dev + prod compose (`backend` + `scheduler`;
prod overlay defaults `LANGSMITH_ENV=prod`). `.env.example` block, deployment-guide §6.5 (enable/disable/
kill-switch, cost caveat, free-tier ceiling, data egress). Validated via `docker compose config` — default
off in dev, `env=prod` in the prod merge.

## The Brutal Truth

Because the stack is already LangChain + LangGraph, tracing is **config, not engineering** — env vars
auto-instrument every `ChatOpenAI` call with zero code change. The only real work was gating,
run↔trace correlation, and pulling the non-LLM collector into the tree. Resisted scope creep: online
LLM-judge evaluators and offline eval datasets were explicitly deferred (heavy recurring cost, no day-one
value).

Code review surfaced and I applied three fixes: pinned `langsmith` explicitly (it was only transitive,
yet `nodes_collector` now imports it directly — latent contract risk), dropped the pointless
`configure_tracing()` from the no-LLM `live_poller` (its compose service intentionally omits `LANGSMITH_*`,
so the call implied a capability that could never fire), and made the env-write atomic.

**Working-tree surprise:** the session opened reporting a clean tree, but `system-architecture.md` (a
rewrite) and 5 deleted `docs/` files were already present — unrelated to this task. Did not sweep them
into the commit; staged only the 19 LangSmith files explicitly and flagged the rest to the user.

## Technical Details

- langchain-core 1.4.8 reads canonical `LANGSMITH_*` env names — no legacy `LANGCHAIN_*` aliases needed.
- `langsmith` 0.8.17 confirmed under `uv`; promoted to explicit `pyproject.toml` dep, `uv.lock` synced.
- `@traceable` is a transparent pass-through when tracing is off (~63µs/call; once-per-run = negligible).
  With tracing on + unreachable endpoint, background ingest fails to stderr but never raises into the node.
- LangSmith dollar charts assume OpenAI pricing → misprice DeepSeek. `agent_runs.cost_usd` stays canonical.
- Tests: backend suite **148 passed** (5 new), keyless — CI stays untraced.

## Remaining (manual, user-only)

1. LangSmith account + `worldcup-2026` project + API key into VM `.env`.
2. One real-key run → confirm `collector→analyst→editor` trace tree + `run_id` correlation.
3. Monitoring dashboard + error-rate **email** alert (documented in deployment-guide §6.5).

## Deferred backlog

Online fact-grounding evaluator (LLM-judge on prod briefs); offline brief-quality dataset + CI regression
evals.
