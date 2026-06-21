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


def merge_intelligence(intelligence: dict | None, stake_groups: list[dict] | None) -> dict:
    """Attach deterministic per-team scenario `rows` (from collector facts) onto
    the LLM's `group_scenarios` by group_name. Groups the LLM emitted without a
    matching deterministic group are dropped (no rows to ground them)."""
    merged = dict(intelligence or {})
    rows_by_group = {
        g.get("group_name"): g.get("rows", [])
        for g in (stake_groups or [])
        if g.get("group_name")
    }
    out_scenarios = []
    for sc in merged.get("group_scenarios") or []:
        rows = rows_by_group.get(sc.get("group_name"))
        if rows is None:
            continue
        out_scenarios.append({**sc, "rows": rows})
    merged["group_scenarios"] = out_scenarios
    return merged


def run_pipeline(target_date: date) -> int:
    """Run the brief pipeline for *target_date*. Returns 0 on success, 1 on failure."""
    from app.config import settings
    from app.data.repository import (
        insert_agent_run,
        make_session_factory,
        prune_logs,
        upsert_article,
    )
    from app.logging_config import configure_logging
    from app.observability import configure_tracing
    from app.pipeline.graph import build_graph

    configure_logging()
    configure_tracing()

    # Daily cadence is sufficient to bound the app_logs window; prune failures
    # must never abort the run.
    try:
        with make_session_factory()() as session:
            removed = prune_logs(session, settings.LOG_RETENTION_DAYS)
        if removed:
            log.info("Pruned %d log rows older than %d days", removed, settings.LOG_RETENTION_DAYS)
    except Exception as exc:
        log.warning("Log prune skipped: %s", exc)

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

    # Fetch fresh data first (collect → brief). Non-fatal: on a missing API key
    # or transient fetch failure we proceed with existing DB data rather than
    # skipping the brief entirely.
    from app.data.collect import run as collect_run

    try:
        rc = collect_run(target_date)
        if rc != 0:
            log.warning("Collector returned %d for %s — proceeding with existing DB data", rc, target_date)
    except Exception as exc:
        log.warning("Collector raised (%s) — proceeding with existing DB data", exc)

    try:
        graph = build_graph()
        # Per-node retry inside each node handles transient LLM errors.
        # Wrapping the full graph would re-run collector+analyst (paid calls) on editor failure.
        # config metadata/tags correlate the LangSmith trace with this agent_runs row
        # (run_id); ignored when tracing is off.
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
            merged_intelligence = merge_intelligence(
                final_state.get("intelligence"),
                (final_state.get("computed_facts") or {}).get("stake_groups"),
            )
            article = {**final_state["article"], "intelligence": merged_intelligence}
            upsert_article(session, article, status="published", brief_date=target_date)
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


def _today_in_brief_tz() -> date:
    from zoneinfo import ZoneInfo
    from app.config import settings
    return datetime.now(tz=ZoneInfo(settings.BRIEF_TIMEZONE)).date()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WC 2026 brief pipeline for a date")
    parser.add_argument(
        "--date",
        type=_parse_date,
        default=None,
        help="YYYY-MM-DD (defaults to today in BRIEF_TIMEZONE)",
    )
    args = parser.parse_args()
    target = args.date or _today_in_brief_tz()

    from app.logging_config import configure_logging, stop_logging
    from app.observability import configure_tracing

    configure_logging()
    configure_tracing()
    try:
        rc = run_pipeline(target)
    finally:
        stop_logging()  # flush buffered records before this short-lived process exits
    sys.exit(rc)


if __name__ == "__main__":
    main()
