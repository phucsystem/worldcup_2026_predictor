"""Standalone live-score poller.

A lightweight, long-running loop (its own process/container) that refreshes
in-play match scores/minute by polling API-Football's `?live=all` — but only
while a fixture is actually in its kickoff window. It NEVER runs the standings
math or the LLM brief pipeline; it only upserts score/status/elapsed.

Run with:  python -m app.pipeline.live_poller
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy import select

from app.config import settings
from app.data.api_football import APIFootballClient
from app.data.collect import collect_live
from app.data.repository import make_session_factory, matches_table

log = logging.getLogger(__name__)


def should_poll_now(
    kickoffs: Iterable[Optional[datetime]],
    now: datetime,
    window: timedelta | None = None,
) -> bool:
    """True if any kickoff is within [now - window, now] — i.e. a match has
    started and could still be in play. Pure; None kickoffs are ignored."""
    if window is None:
        window = timedelta(hours=settings.LIVE_WINDOW_HOURS)
    for ko in kickoffs:
        if ko is None:
            continue
        if ko.tzinfo is None:
            ko = ko.replace(tzinfo=timezone.utc)
        if now - window <= ko <= now:
            return True
    return False


def _kickoffs(session_factory) -> list[datetime]:
    with session_factory() as session:
        rows = session.execute(
            select(matches_table.c.kickoff_utc).where(matches_table.c.kickoff_utc.isnot(None))
        ).all()
    return [r[0] for r in rows]


def main() -> None:
    import signal
    import sys

    from app.logging_config import configure_logging, stop_logging

    configure_logging()
    # No configure_tracing() here: the poller never runs the LLM graph, so there
    # is nothing to trace (its compose service intentionally omits LANGSMITH_*).
    # `docker stop` sends SIGTERM, on which atexit does NOT run — flush + exit so
    # the final buffered log batch isn't lost on every restart/redeploy.
    signal.signal(signal.SIGTERM, lambda *_: (stop_logging(), sys.exit(0)))

    if not settings.API_FOOTBALL_KEY:
        log.error("API_FOOTBALL_KEY not set — live poller cannot run")
        return

    client = APIFootballClient()
    session_factory = make_session_factory()
    log.info(
        "Live poller started (poll=%ss idle=%ss window=%sh)",
        settings.LIVE_POLL_SECONDS,
        settings.IDLE_SLEEP_SECONDS,
        settings.LIVE_WINDOW_HOURS,
    )

    while True:
        now = datetime.now(tz=timezone.utc)
        try:
            if should_poll_now(_kickoffs(session_factory), now):
                collect_live(session_factory, client)
                sleep = settings.LIVE_POLL_SECONDS
            else:
                sleep = settings.IDLE_SLEEP_SECONDS
        except Exception as exc:  # never let a transient API/DB error kill the loop
            log.warning("Live poll failed: %s", exc)
            sleep = settings.IDLE_SLEEP_SECONDS
        time.sleep(sleep)


if __name__ == "__main__":
    main()
