---
title: LangSmith Agent Observability
description: ''
status: completed
priority: P2
branch: test/e2e-robot-framework
tags: []
blockedBy: []
blocks: []
created: '2026-06-21T20:44:13.117Z'
createdBy: 'ck:plan'
source: skill
---

# LangSmith Agent Observability

## Overview

Add LangSmith tracing + built-in monitoring (dashboards + email alert) over the existing LangGraph
brief pipeline (`Collector → Analyst → Editor`, DeepSeek via `langchain-openai`). Env-gated and CI-safe:
flag off / no key → byte-identical runs, zero overhead. The hand-rolled `agent_runs` + `app_logs`
tooling stays authoritative for the frontend; LangSmith layers trace-level depth on top, correlated by
`run_id`. Approach **B** from the brainstorm: env-var tracing + a small `observability.py` bootstrap that
mirrors `configure_logging()` + `@traceable` on the non-LLM collector for a full trace tree.

**Source brainstorm:** [`ck_plans/reports/260622-langsmith-observability-brainstorm.md`](../reports/260622-langsmith-observability-brainstorm.md)

**Explicitly OUT of scope (deferred):** online LLM-judge evaluators; offline eval datasets / CI
regression evals; self-hosted LangSmith; replacing `agent_runs`/`app_logs` cost tracking; frontend changes.

## Acceptance criteria (whole plan)

- Local run with `LANGSMITH_TRACING=true` + key → one trace tree in LangSmith: `collector → analyst →
  editor` with prompts, token counts, per-node latency, and retry attempts visible.
- Each trace carries `run_id` (matching the `agent_runs` row) and an `env` tag.
- Flag off **or** no key → pipeline runs identically, zero tracing overhead, **no errors**; `pytest` passes
  with no LangSmith key present (CI stays keyless).
- LangSmith monitoring dashboard shows latency / cost / error trend; an email alert fires on the
  error-rate threshold.
- `agent_runs`, `app_logs`, and the frontend dashboard are untouched.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Config & Tracing Bootstrap](./phase-01-config-tracing-bootstrap.md) | Completed |
| 2 | [Run Correlation & Trace Tree](./phase-02-run-correlation-trace-tree.md) | Completed |
| 3 | [Deploy Wiring & Monitoring](./phase-03-deploy-wiring-monitoring.md) | Completed |

Phases are sequential: 2 depends on 1 (needs the bootstrap + settings); 3 depends on 1–2 (wires the
verified mechanism into deploy + the LangSmith UI).

## Dependencies

- **Out-of-band prerequisite:** a LangSmith account + project + API key (provisioned into the VM `.env`).
  Code lands behind a default-off flag, so this is not a hard blocker for merging Phases 1–2.
- **Soft file overlap (not blocking):** `260621-azure-vm-deploy` (in-progress) also edits
  `docker-compose.prod.yml` and the VM `.env`. LangSmith env passthrough is purely additive — coordinate
  the prod-compose edit (Phase 3) to avoid a merge clash, but neither plan blocks the other.

## Key constraints

- CI-safe: mirror the existing `make_client()` no-key pattern and `LOG_DB_ENABLED` gating.
- Never raise into the pipeline (tracing failures are swallowed, like `DBLogHandler`).
- Env-var toggle without redeploy; no secrets committed.
- Follow existing conventions: pydantic `Settings`, the `configure_logging()` bootstrap shape, lazy imports.
