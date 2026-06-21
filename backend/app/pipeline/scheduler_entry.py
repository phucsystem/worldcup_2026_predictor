"""Scheduled job entrypoint for the Azure Container Apps Job.

The Azure cron fires at two UTC candidate hours that cover 07:00
Australia/Melbourne across both timezone offsets:
  - 20:00 UTC → 07:00 AEDT (UTC+11, Oct–Apr)
  - 21:00 UTC → 07:00 AEST (UTC+10, Apr–Oct)

The DST guard below confirms it is actually 07:00 in the local timezone
before running, making the double-trigger safe (one fires, one no-ops).
FORCE_RUN=1 or --force bypasses the guard for manual/testing use.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)


def is_brief_time(now_utc: datetime, tz_name: str = "Australia/Melbourne") -> bool:
    """Return True if *now_utc* corresponds to 07:00 in *tz_name*.

    Pure function — no I/O, safe to unit-test with fixed datetimes.
    """
    local_dt = now_utc.astimezone(ZoneInfo(tz_name))
    return local_dt.hour == 7


def main() -> None:
    from app.config import settings
    from app.logging_config import configure_logging, stop_logging
    from app.observability import configure_tracing
    from app.pipeline.run import run_pipeline

    configure_logging()
    configure_tracing()

    try:
        force = os.environ.get("FORCE_RUN", "").strip() == "1" or "--force" in sys.argv

        now_utc = datetime.now(tz=timezone.utc)

        if not force and not is_brief_time(now_utc, settings.BRIEF_TIMEZONE):
            local_time = now_utc.astimezone(ZoneInfo(settings.BRIEF_TIMEZONE))
            log.info(
                "TZ guard: current time in %s is %s (hour=%d) — not 07:00, skipping.",
                settings.BRIEF_TIMEZONE,
                local_time.strftime("%H:%M"),
                local_time.hour,
            )
            rc = 0
        else:
            local_dt = now_utc.astimezone(ZoneInfo(settings.BRIEF_TIMEZONE))
            brief_date = local_dt.date()
            log.info("TZ guard passed — running pipeline for %s", brief_date)
            rc = run_pipeline(brief_date)
    finally:
        stop_logging()  # flush before this short-lived job exits
    sys.exit(rc)


if __name__ == "__main__":
    main()
