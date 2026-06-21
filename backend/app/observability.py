"""Env-gated LangSmith tracing bootstrap.

`configure_tracing()` mirrors `configure_logging()`: one idempotent call per
process that turns LangSmith tracing on *only* when both the flag and a key are
present, and is a silent no-op otherwise. It never raises into the caller —
tracing must never break the pipeline.

LangChain's tracer reads ``LANGSMITH_*`` from ``os.environ`` lazily on each
LLM/graph call, so exporting the vars once per process is enough; node code is
untouched. (langchain-core 1.x reads the ``LANGSMITH_*`` names; no legacy
``LANGCHAIN_*`` aliases needed.)
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

_configured = False


def configure_tracing() -> bool:
    """Idempotently enable LangSmith tracing from settings. Returns True if
    tracing is enabled. Safe to call from any entrypoint, repeatedly."""
    global _configured
    if _configured:
        return os.environ.get("LANGSMITH_TRACING") == "true"
    try:
        from app.config import settings

        if not (settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY):
            _configured = True
            return False

        # Build the full env map first, then apply atomically — so a failure can
        # never leave a half-set (TRACING=true but no key) environment.
        env = {
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_API_KEY": settings.LANGSMITH_API_KEY,
            "LANGSMITH_PROJECT": settings.LANGSMITH_PROJECT,
            "LANGSMITH_ENDPOINT": settings.LANGSMITH_ENDPOINT,
        }
        os.environ.update(env)
        log.info(
            "LangSmith tracing enabled (project=%s env=%s)",
            settings.LANGSMITH_PROJECT,
            settings.LANGSMITH_ENV,
        )
        _configured = True
        return True
    except Exception as exc:  # tracing must never break the app
        log.warning("LangSmith tracing setup skipped: %s", exc)
        _configured = True
        return False
