---
phase: 3
title: Deploy Wiring & Monitoring
status: completed
effort: ''
---

# Phase 3: Deploy Wiring & Monitoring

## Overview

Wire the `LANGSMITH_*` env through docker-compose (dev + prod) to the services that run the pipeline,
document the vars, and set up the LangSmith UI side: project, monitoring dashboard, and one email alert.
Close with an end-to-end verification of the whole-plan acceptance criteria.

## Requirements

- Functional: `scheduler` and `backend` services receive `LANGSMITH_*` env in both compose files (the
  `backend` runs the admin HTTP triggers, which run the pipeline). Defaults remain off.
- Non-functional: a stack with no LangSmith vars set behaves exactly as today.

## Architecture

Compose passes the four vars through with safe defaults (`${LANGSMITH_TRACING:-false}`, empty key). The
key lives only in `.env` (dev) / VM `.env` (prod) — never committed. Monitoring + alerting are LangSmith
SaaS features configured once in the UI, not in code.

## Related Code Files

- Modify: `docker-compose.yml` (add `LANGSMITH_*` to `scheduler` and `backend` env)
- Modify: `docker-compose.prod.yml` (same — coordinate with `260621-azure-vm-deploy`)
- Modify: `.env.example` (document the four vars, default `LANGSMITH_TRACING=false`)
- Modify: `ck_docs/deployment-guide.md` (add an "Enabling LangSmith tracing" section)

## Implementation Steps

1. **`docker-compose.yml`** — under both `scheduler.environment` and `backend.environment`:
   ```yaml
   LANGSMITH_TRACING: ${LANGSMITH_TRACING:-false}
   LANGSMITH_API_KEY: ${LANGSMITH_API_KEY:-}
   LANGSMITH_PROJECT: ${LANGSMITH_PROJECT:-worldcup-2026}
   LANGSMITH_ENV: ${LANGSMITH_ENV:-dev}
   ```
2. **`docker-compose.prod.yml`** — same block; set `LANGSMITH_ENV` default to `prod`. Rebase on the
   azure-vm-deploy branch's compose edits first to avoid a clash.
3. **`.env.example`** — add a documented block:
   ```bash
   # LangSmith observability (optional). Leave TRACING=false to fully disable.
   LANGSMITH_TRACING=false
   LANGSMITH_API_KEY=
   LANGSMITH_PROJECT=worldcup-2026
   LANGSMITH_ENV=dev
   ```
4. **`ck_docs/deployment-guide.md`** — short section: what tracing gives you, how to enable (set the two
   non-default vars in VM `.env`, redeploy/restart `scheduler`+`backend`), the free-tier ~5k traces/mo
   ceiling + that `LANGSMITH_TRACING=false` is the kill switch, and the note that `agent_runs.cost_usd`
   remains canonical for cost (LangSmith's dollar figure misprices DeepSeek).
5. **LangSmith UI (one-time, manual — document in the deployment guide):**
   - Create project `worldcup-2026`.
   - Confirm the Monitoring tab shows trace volume / latency / error rate after the first traced run.
   - Add an alert: error-rate threshold over a rolling window → **email** notification.
6. **End-to-end verification** (the whole-plan gate):
   - Keyless `uv run pytest` green.
   - Dev run with flag on → trace tree + `run_id` correlation confirmed (carried from Phase 2).
   - `docker compose config` resolves with and without `LANGSMITH_*` set (no breakage when unset).
   - Toggle `LANGSMITH_TRACING=false` → run produces no traces, no errors.

## Success Criteria

- [ ] `scheduler` + `backend` receive `LANGSMITH_*` in dev and prod compose; stack runs unchanged when unset.
- [ ] `.env.example` documents the vars; no key committed anywhere.
- [ ] `deployment-guide.md` explains enable/disable, the trace ceiling, and the canonical-cost note.
- [ ] LangSmith project + monitoring dashboard live; email alert configured and test-fires.
- [ ] Full acceptance criteria in `plan.md` satisfied; `agent_runs`/`app_logs`/frontend untouched.

## Risk Assessment

- **Merge clash on `docker-compose.prod.yml`** with `260621-azure-vm-deploy`. Mitigation: rebase on that
  branch before editing; the LangSmith block is additive and isolated.
- **Free-tier trace exhaustion** from the live poller + 30-min dev cadence. Mitigation: documented kill
  switch; if hit, lower cadence or scope tracing to prod-only via `LANGSMITH_TRACING`. Online sampling is
  a later option (deferred).
- **Secret leakage** via committed `.env`. Mitigation: only `.env.example` (empty key) is committed;
  `.gitignore` already excludes `.env` — confirm during implementation.
