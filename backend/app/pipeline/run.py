"""Pipeline runner — callable and CLI entry point.

Usage:
  python -m app.pipeline.run --date YYYY-MM-DD
  from app.pipeline.run import run_pipeline; run_pipeline(some_date)
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
import uuid
from datetime import date, datetime, timezone
from typing import Any, Callable, TypeVar

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

T = TypeVar("T")

_MAX_ATTEMPTS = 3
_BACKOFF_BASE = 2.0  # seconds; delay = base ** attempt (1s, 2s, 4s)


def _with_retry(fn: Callable[[], T], label: str) -> T:
    """Capped exponential backoff for transient API/LLM errors (max 3 attempts)."""
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return fn()
        except Exception as exc:
            if attempt == _MAX_ATTEMPTS - 1:
                raise
            delay = _BACKOFF_BASE ** attempt
            log.warning("%s attempt %d/%d failed (%s); retrying in %.0fs",
                        label, attempt + 1, _MAX_ATTEMPTS, exc, delay)
            time.sleep(delay)
    raise RuntimeError("unreachable")  # pragma: no cover


def _parse_date(val: str) -> date:
    return date.fromisoformat(val)


def run_pipeline(target_date: date) -> int:
    """Run the brief pipeline for *target_date*. Returns 0 on success, 1 on failure."""
    from app.data.repository import insert_agent_run, make_session_factory, upsert_article
    from app.pipeline.graph import build_graph

    run_id = str(uuid.uuid4())
    started_at = datetime.now(tz=timezone.utc)

    initial_state: dict[str, Any] = {
        "brief_date": target_date.isoformat(),
        "matches": [],
        "standings": [],
        "computed_facts": {},
        "intelligence": {},
        "article": {},
        "run_id": run_id,
        "node_timings": {},
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0.0,
        "error": None,
    }

    log.info("Starting pipeline run %s for %s", run_id, target_date)

    try:
        graph = build_graph()
        # Per-node retry inside each node handles transient LLM errors.
        # Wrapping the full graph would re-run collector+analyst (paid calls) on editor failure.
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        finished_at = datetime.now(tz=timezone.utc)
        factory = make_session_factory()
        with factory() as session:
            insert_agent_run(session, {
                "run_id": run_id,
                "brief_date": target_date,
                "started_at": started_at,
                "finished_at": finished_at,
                "node_timings": {},
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "status": "failed",
                "error": str(exc),
            })
        log.error("Pipeline crashed (last-good article preserved): %s", exc)
        return 1

    finished_at = datetime.now(tz=timezone.utc)
    error = final_state.get("error")

    factory = make_session_factory()
    with factory() as session:
        # Publish ONLY after editor succeeds — keeps last-good brief on failure.
        if not error:
            upsert_article(session, final_state["article"], status="published", brief_date=target_date)
            log.info("Article published for %s", target_date)

        insert_agent_run(session, {
            "run_id": run_id,
            "brief_date": target_date,
            "started_at": started_at,
            "finished_at": finished_at,
            "node_timings": final_state.get("node_timings", {}),
            "tokens_in": final_state.get("tokens_in", 0),
            "tokens_out": final_state.get("tokens_out", 0),
            "cost_usd": final_state.get("cost_usd", 0.0),
            "status": "failed" if error else "completed",
            "error": error,
        })

    if error:
        log.error("Pipeline failed (last-good article preserved): %s", error)
        return 1

    log.info(
        "Run complete. tokens_in=%d tokens_out=%d cost=$%.4f timings=%s",
        final_state.get("tokens_in", 0),
        final_state.get("tokens_out", 0),
        final_state.get("cost_usd", 0.0),
        final_state.get("node_timings", {}),
    )
    return 0


# Keep backward-compatible alias used by any existing callers.
run = run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WC 2026 brief pipeline for a date")
    parser.add_argument("--date", required=True, type=_parse_date, help="YYYY-MM-DD")
    args = parser.parse_args()
    sys.exit(run_pipeline(args.date))


if __name__ == "__main__":
    main()
