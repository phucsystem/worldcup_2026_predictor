"""DST-aware timezone guard tests for scheduler_entry.is_brief_time.

Covers both AEST (UTC+10, winter/Jul) and AEDT (UTC+11, summer/Jan).
The tested function is pure — no I/O, injected datetime only.
"""
from datetime import datetime, timezone

import pytest
from zoneinfo import ZoneInfo

from app.pipeline.scheduler_entry import is_brief_time

MELB = "Australia/Melbourne"


# ---------------------------------------------------------------------------
# AEST: UTC+10 (winter — e.g. July)
# 07:00 AEST = 21:00 UTC previous day
# ---------------------------------------------------------------------------

class TestAEST:
    """Australia/Melbourne in standard time (UTC+10)."""

    def _utc(self, hour: int, minute: int = 0) -> datetime:
        # 2026-07-15 is mid-winter → AEST (UTC+10)
        return datetime(2026, 7, 15, hour, minute, tzinfo=timezone.utc)

    def test_07_00_aest_is_brief_time(self):
        # 21:00 UTC = 07:00 AEST
        assert is_brief_time(self._utc(21, 0), MELB) is True

    def test_06_59_aest_is_not_brief_time(self):
        # 20:59 UTC = 06:59 AEST
        assert is_brief_time(self._utc(20, 59), MELB) is False

    def test_08_00_aest_is_not_brief_time(self):
        # 22:00 UTC = 08:00 AEST
        assert is_brief_time(self._utc(22, 0), MELB) is False

    def test_07_30_aest_is_still_brief_time(self):
        # hour check only — 07:30 AEST (21:30 UTC) still hour==7
        assert is_brief_time(self._utc(21, 30), MELB) is True


# ---------------------------------------------------------------------------
# AEDT: UTC+11 (summer — e.g. January)
# 07:00 AEDT = 20:00 UTC previous day
# ---------------------------------------------------------------------------

class TestAEDT:
    """Australia/Melbourne in daylight saving time (UTC+11)."""

    def _utc(self, hour: int, minute: int = 0) -> datetime:
        # 2026-01-15 is mid-summer → AEDT (UTC+11)
        return datetime(2026, 1, 15, hour, minute, tzinfo=timezone.utc)

    def test_07_00_aedt_is_brief_time(self):
        # 20:00 UTC = 07:00 AEDT
        assert is_brief_time(self._utc(20, 0), MELB) is True

    def test_06_59_aedt_is_not_brief_time(self):
        # 19:59 UTC = 06:59 AEDT
        assert is_brief_time(self._utc(19, 59), MELB) is False

    def test_08_00_aedt_is_not_brief_time(self):
        # 21:00 UTC = 08:00 AEDT
        assert is_brief_time(self._utc(21, 0), MELB) is False

    def test_aest_trigger_fires_at_08_aedt_not_07(self):
        # The AEST trigger (21:00 UTC) fires at 08:00 AEDT — must be a no-op
        assert is_brief_time(self._utc(21, 0), MELB) is False

    def test_aedt_trigger_fires_at_07_aest_not_07(self):
        # The AEDT trigger (20:00 UTC) fires at 06:00 AEST — must be a no-op
        # 2026-07-15: 20:00 UTC = 06:00 AEST
        aest_dt = datetime(2026, 7, 15, 20, 0, tzinfo=timezone.utc)
        assert is_brief_time(aest_dt, MELB) is False
