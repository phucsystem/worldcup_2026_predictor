"""Unit tests for statistics-backfill selection — no DB, no network.

Statistics-payload shaping (raw → MatchStat bars) is tested separately in
test_fixture_statistics_shaping.py once the API surface lands (Phase 3); here we
only cover the once-only backfill guard, mirroring test_match_events.py.
"""

from app.api.fixtures import select_fixtures_needing_statistics
from app.data.models import Match

HOME = "France"
AWAY = "Brazil"


def _match(fid, status):
    return Match(
        fixture_id=fid, group_name=None, home_team=HOME, away_team=AWAY,
        home_score=None, away_score=None, status=status, kickoff_utc=None,
    )


class TestSelectFixturesNeedingStatistics:
    def test_finished_without_stats_is_selected(self):
        assert select_fixtures_needing_statistics([_match(1, "FT")], existing=set()) == [1]

    def test_finished_with_stats_is_skipped(self):
        assert select_fixtures_needing_statistics([_match(1, "FT")], existing={1}) == []

    def test_not_started_is_skipped(self):
        assert select_fixtures_needing_statistics([_match(1, "NS")], existing=set()) == []

    def test_live_is_skipped(self):
        # in-play matches are not backfilled on the daily path
        assert select_fixtures_needing_statistics([_match(1, "2H")], existing=set()) == []

    def test_aet_and_pen_are_finished(self):
        matches = [_match(1, "AET"), _match(2, "PEN")]
        assert select_fixtures_needing_statistics(matches, existing=set()) == [1, 2]

    def test_mixed_set(self):
        matches = [_match(1, "FT"), _match(2, "NS"), _match(3, "FT"), _match(4, "FT")]
        assert select_fixtures_needing_statistics(matches, existing={3}) == [1, 4]
