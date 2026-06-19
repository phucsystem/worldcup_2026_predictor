---
phase: 5
title: "Scheduling & Reliability"
status: done
priority: P1
effort: "1-2d"
dependencies: [3, 4]
---

# Phase 5: Scheduling & Reliability

## Overview
Automate the pipeline as a cron-scheduled Azure Container Apps Job at 7:00 AM Australia/Melbourne, with idempotency, retries, and full run logging.

## Requirements
- Functional: the brief generates daily with zero manual steps; re-running a date is safe (no duplicates); failures are captured with status + error.
- Non-functional: DST-aware schedule; observable via `agent_runs`.

## Architecture
- **Azure Container Apps Job**, trigger type `Schedule`, cron expression for 07:00 Australia/Melbourne.
  - Container Apps cron is UTC → compute UTC equivalents for AEST (UTC+10) and AEDT (UTC+11), or run hourly with a TZ guard in-process. **Decision: in-process TZ check** (job triggers at the two candidate UTC hours; code confirms it's 07:00 in Australia/Melbourne before running) to handle DST without redeploys.
- Idempotency: pipeline keyed by `brief_date`; article + standings upsert; a same-day re-run replaces, never duplicates.
- Retries: per-node retry (transient API/LLM errors) with capped backoff; on terminal failure, write `agent_runs.status='failed'` + error, exit non-zero.
- **Failure recovery (keep last good):** a failed/partial run must **not** publish a broken brief. Article is only marked `status='published'` after the Editor node succeeds; the site (Phase 4) keeps serving the last published brief. On failure the prior brief stays live. <!-- Updated: Validation Session 1 - keep prior + manual re-trigger -->
- **Manual re-trigger:** the same `python -m app.pipeline.run --date <d>` entrypoint can be invoked on-demand (locally or via Azure "run job now") to regenerate a failed/bad brief; idempotent upsert replaces it.
- Run record: every execution writes `agent_runs` (success or failure) for observability.

## Related Code Files
- Create: `backend/app/pipeline/scheduler_entry.py` (TZ guard + invoke run), `infra/container-app-job.bicep` (or config), `backend/Dockerfile.job`
- Modify: `backend/app/pipeline/run.py` (retry/backoff, exit codes), `backend/app/data/repository.py` (idempotent guarantees)

## Implementation Steps
1. `scheduler_entry.py`: check current time in Australia/Melbourne == 07:00; if not, no-op exit 0.
2. Add retry/backoff around node calls in `run.py`; ensure `agent_runs` written on failure paths.
3. Verify idempotency: re-run same date → single article/standings snapshot.
4. `Dockerfile.job` for the job image; `container-app-job.bicep` schedule trigger (two UTC candidate hours).
5. Local test: simulate scheduled invocation; force-fail a node → confirm `agent_runs.status='failed'`.

## Success Criteria
- [ ] Scheduled job triggers and produces the daily brief unattended.
- [ ] Re-run of a date yields no duplicate rows.
- [ ] Forced node failure → `agent_runs.status='failed'` + error captured, non-zero exit, **and no broken brief published** (site still shows last good one).
- [ ] Manual re-trigger of a failed date regenerates and publishes the brief.
- [ ] Brief publishes at 07:00 Australia/Melbourne across a DST boundary.

## Risk Assessment
- Container Apps cron is UTC-only → in-process TZ guard avoids DST redeploys (chosen).
- Partial pipeline failure mid-run → idempotent upserts + retries make re-run safe.
- Job cold start / image size → slim Python base image.
