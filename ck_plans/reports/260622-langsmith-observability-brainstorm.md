# Brainstorm — Agent Observability with LangSmith

- **Date:** 2026-06-22
- **Topic:** Set up agent observability with LangSmith for the LangGraph brief pipeline
- **Status:** Approved → proceed to `/ck:plan` (default mode)
- **Chosen approach:** B (env-var tracing + small `observability.py` bootstrap + `@traceable` glue)

---

## Problem statement

Pipeline is a LangGraph `StateGraph` (`Collector → Analyst → Editor`) narrating DeepSeek-generated
intelligence. Current visibility = hand-rolled: `agent_runs` row (run_id, node_timings, tokens, cost,
status) + `app_logs`. Missing = trace-level depth: actual prompts, per-LLM-call I/O, retries, per-node
latency, live monitoring dashboards/alerts. Goal: add LangSmith on top without disturbing existing tooling.

## Requirements (locked)

1. **Expected output:** LangSmith env wiring (`config.py`, compose, `.env.example`); a new
   `observability.py` bootstrap; per-run metadata/tags on `graph.invoke`; `@traceable` on collector glue;
   a LangSmith project + monitoring dashboards + one email alert; a short docs section.
2. **Acceptance criteria:** local run with flag on emits one trace tree (collector→analyst→editor, prompts,
   tokens, latency, retries); each trace carries `run_id` + `env` tag matching `agent_runs`; flag off / no
   key → identical run, zero overhead, no errors (CI keyless); monitoring dashboard live; email alert fires
   on error-rate threshold; `agent_runs`/`app_logs`/frontend untouched.
3. **Scope OUT (deferred):** online LLM-judge evaluators; offline eval datasets / CI regression evals;
   self-hosted LangSmith; replacing the hand-rolled cost/token tracking; frontend changes.
4. **Non-negotiable constraints:** CI-safe (mirror `make_client` no-key + `LOG_DB_ENABLED` gating patterns);
   never raise into the pipeline; env-var toggle without redeploy; no secrets committed; follow pydantic
   `Settings` + `configure_logging()` conventions.
5. **Touchpoints:** `backend/app/config.py`, `backend/app/observability.py` (new),
   `backend/app/pipeline/run.py`, `backend/app/pipeline/nodes_collector.py`,
   `backend/app/pipeline/scheduler_entry.py`, `backend/app/main.py`, `docker-compose.yml`,
   `docker-compose.prod.yml`, `.env.example`, `ck_docs/deployment-guide.md`.

## Key insight

Stack is LangChain + LangGraph → tracing is **config, not engineering**. `LANGSMITH_TRACING=true` +
`LANGSMITH_API_KEY` (+ project) auto-instruments every node + `ChatOpenAI` call with zero code change.
The engineering is only: gating, run↔trace correlation, and pulling non-LLM steps into the trace tree.

## Approaches evaluated

| | A — pure env-var | B — bootstrap + `@traceable` ⭐ | C — `langsmith.Client` |
|---|---|---|---|
| Effort | ~½ day | ~1 day | ~2 day |
| Trace coverage | graph nodes + LLM only | full run tree (incl. collector/DB glue) | full + programmatic |
| Convention fit | minimal | mirrors `configure_logging()` | new patterns |
| Extensible to evals | weak | clean seam | strong |
| Verdict | viable minimum | **chosen** | overkill now |

## Chosen design (B)

- `config.py`: add `LANGSMITH_TRACING: bool=False`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENV`.
- `observability.py` (new): `configure_tracing()` — idempotent, env-gated, swallows own errors; sets the
  `LANGSMITH_*` env vars LangChain reads when flag+key present, else no-op. Called beside `configure_logging()`
  in `run.py`, `scheduler_entry.py`, `main.py`.
- `run.py`: `graph.invoke(initial_state, config={"run_name": f"brief-{date}", "metadata": {"run_id", "brief_date",
  "env"}, "tags": [env, "pipeline"]})` — the trace↔`agent_runs` link.
- `nodes_collector.py`: `@traceable` so the non-LLM collector is a span in the same tree.
- compose (both files): pass `LANGSMITH_*` to `scheduler` **and** `backend` (admin HTTP triggers run the pipeline).
- `.env.example` + `ck_docs/deployment-guide.md`: document the four vars (default `LANGSMITH_TRACING=false`).
- LangSmith UI (one-time manual): create project, confirm monitoring dashboard, add email alert on error-rate.

**Bonus:** flag-on auto-traces any `ChatOpenAI` in `verdict.py` / `live_poller` for free.

## Risks / caveats

- **LangSmith cost charts assume OpenAI pricing** → mispriced for DeepSeek. Decision: treat
  `agent_runs.cost_usd` as canonical, ignore LangSmith dollar figure (less to maintain).
- **Free-tier ~5k traces/mo** reachable via live poller + 30-min dev cadence. Control = env flag + optional
  sampling. Note in plan.
- **Data egress:** full prompts/outputs leave to SaaS — accepted (public football data + narration, low risk).
- **No new dependency:** `langsmith` arrives transitively via `langchain-core`; pin explicitly only if
  Approach C / evaluators adopted later.

## Success metrics

- First flag-on run visible end-to-end in LangSmith within minutes; trace carries matching `run_id`.
- Flag-off CI run stays green and untraced.
- Dashboard surfaces latency/cost/error trend over ≥1 day; alert delivers a test email.

## Next steps

1. `/ck:plan` (default) from this report → phased implementation plan.
2. Provision LangSmith account + project + API key (out-of-band, into VM `.env`).
3. Deferred backlog: online fact-grounding evaluator; offline brief-quality dataset + CI regression evals.
