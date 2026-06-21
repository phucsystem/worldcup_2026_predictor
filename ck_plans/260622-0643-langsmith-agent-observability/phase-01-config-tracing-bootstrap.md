---
phase: 1
title: Config & Tracing Bootstrap
status: completed
effort: ''
---

# Phase 1: Config & Tracing Bootstrap

## Overview

Add LangSmith settings to the pydantic `Settings` and a new `app/observability.py` exposing
`configure_tracing()` — an idempotent, env-gated, never-raising bootstrap that mirrors
`configure_logging()`. Wire it into every process entrypoint beside the logging bootstrap. This is the
foundation: after this phase, tracing turns on/off purely by env, and is a no-op (zero overhead, no
errors) when the flag is off or the key is absent.

## Requirements

- Functional: when `LANGSMITH_TRACING=true` **and** a key is present, the LangChain env vars LangSmith
  reads (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`) are set in the
  process so any `ChatOpenAI` call auto-traces; otherwise a no-op.
- Non-functional: idempotent (safe to call repeatedly, incl. uvicorn reload); never raises into the
  caller; no new pip dependency (`langsmith` arrives transitively via `langchain-core`).

## Architecture

`config.py` gains four fields (all optional / default-off). `observability.py::configure_tracing()` reads
`settings`, and **only when enabled** exports the `LANGSMITH_*` env vars that LangChain's tracer checks at
call time. LangChain auto-instruments from env — no client object to hold. The function is the single
gating choke point, exactly like `configure_logging()` is for logs.

Why env-export rather than passing a client around: LangChain's tracer reads `os.environ` lazily on each
LLM/graph call, so setting the vars once per process is sufficient and keeps node code untouched.

## Related Code Files

- Create: `backend/app/observability.py`
- Create: `backend/tests/test_observability.py`
- Modify: `backend/app/config.py` (add 4 settings)
- Modify: `backend/app/pipeline/run.py` (call `configure_tracing()` after `configure_logging()` — both sites)
- Modify: `backend/app/pipeline/scheduler_entry.py` (same)
- Modify: `backend/app/pipeline/live_poller.py` (same)
- Modify: `backend/app/main.py` (same — FastAPI, covers admin HTTP triggers)

## Implementation Steps

1. **`config.py`** — add to `Settings`:
   ```python
   LANGSMITH_TRACING: bool = False
   LANGSMITH_API_KEY: Optional[str] = None
   LANGSMITH_PROJECT: str = "worldcup-2026"
   LANGSMITH_ENV: str = "dev"          # tag value: dev | prod; not a LangChain var
   LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
   ```
2. **`observability.py`** — implement `configure_tracing()`:
   ```python
   from __future__ import annotations
   import logging, os
   log = logging.getLogger(__name__)
   _configured = False

   def configure_tracing() -> bool:
       """Idempotent, env-gated LangSmith bootstrap. Returns True if tracing was enabled.
       Never raises into the caller."""
       global _configured
       if _configured:
           return os.environ.get("LANGSMITH_TRACING") == "true"
       try:
           from app.config import settings
           if not (settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY):
               _configured = True
               return False
           os.environ["LANGSMITH_TRACING"] = "true"
           os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
           os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
           os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
           log.info("LangSmith tracing enabled (project=%s env=%s)",
                    settings.LANGSMITH_PROJECT, settings.LANGSMITH_ENV)
           _configured = True
           return True
       except Exception as exc:  # tracing must never break the app
           log.warning("LangSmith tracing setup skipped: %s", exc)
           _configured = True
           return False
   ```
   Note: also set `LANGCHAIN_TRACING_V2`/`LANGCHAIN_API_KEY` aliases only if the installed
   `langchain-core` version predates the `LANGSMITH_*` names — verify the resolved version during
   implementation and pick whichever the tracer actually reads (don't set both blindly).
3. **Wire entrypoints** — add `from app.observability import configure_tracing; configure_tracing()`
   immediately after each `configure_logging()` call in `run.py` (run_pipeline + main), `scheduler_entry.py`,
   `live_poller.py`, and `main.py`. (Skip `collect.py` — collector has no LLM, nothing to trace.)
4. **Test** `test_observability.py`:
   - flag off → `configure_tracing()` returns `False`, `LANGSMITH_TRACING` not set to `"true"`.
   - flag on + fake key (monkeypatched settings) → returns `True`, env vars set.
   - second call is a no-op (idempotent).
   - settings import failure (monkeypatched to raise) → returns `False`, no exception propagates.

## Success Criteria

- [ ] `configure_tracing()` returns `False` and sets nothing when flag off or key absent.
- [ ] With flag on + key, the four `LANGSMITH_*` env vars are exported; second call is a no-op.
- [ ] Function never raises (covered by a test that forces an internal error).
- [ ] `uv run pytest` passes with no LangSmith key in the environment.
- [ ] Every entrypoint that calls `configure_logging()` (except `collect.py`) also calls `configure_tracing()`.

## Risk Assessment

- **Env-var name drift between langchain versions** (`LANGSMITH_*` vs legacy `LANGCHAIN_*`). Mitigation:
  check the resolved `langchain-core` version at implementation time; set the names the installed tracer
  reads. Low risk — recent versions accept `LANGSMITH_*`.
- **Double-config under uvicorn reload.** Mitigated by the `_configured` idempotency guard.
