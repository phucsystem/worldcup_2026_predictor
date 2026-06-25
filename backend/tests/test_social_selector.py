"""Unit tests for select_fixtures_needing_social.

Pure function — no DB/network/LLM. Unlike the once-only forecast selector this
one is refresh-aware (keeps already-populated upcoming fixtures), window-bounded
(SOCIAL_LOOKAHEAD_HOURS), and count-capped (SOCIAL_MAX_FIXTURES_PER_RUN).
"""
from datetime import datetime, timedelta, timezone

from app.api.fixtures import select_fixtures_needing_social
from app.config import settings
from app.data.models import Match

NOW = datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc)


def _match(fid, *, group_name="G", status="NS", kickoff=None, social=None):
    return Match(
        fixture_id=fid, group_name=group_name, home_team="Argentina", away_team="Mexico",
        home_score=None, away_score=None, status=status, kickoff_utc=kickoff,
        social_json=social,
    )


def test_upcoming_group_fixture_in_window_is_selected():
    m = _match(1, kickoff=NOW + timedelta(hours=6))
    assert select_fixtures_needing_social([m], NOW) == [1]


def test_already_populated_fixture_is_kept_refresh_aware():
    # The deliberate deviation from forecast: highlights re-curate daily.
    m = _match(1, kickoff=NOW + timedelta(hours=6), social={"highlights": [{"x": 1}]})
    assert select_fixtures_needing_social([m], NOW) == [1]


def test_finished_fixture_is_excluded():
    m = _match(1, status="FT", kickoff=NOW + timedelta(hours=6))
    assert select_fixtures_needing_social([m], NOW) == []


def test_knockout_fixture_without_group_is_excluded():
    m = _match(1, group_name=None, kickoff=NOW + timedelta(hours=6))
    assert select_fixtures_needing_social([m], NOW) == []


def test_fixture_beyond_lookahead_window_is_excluded():
    m = _match(1, kickoff=NOW + timedelta(hours=settings.SOCIAL_LOOKAHEAD_HOURS + 1))
    assert select_fixtures_needing_social([m], NOW) == []


def test_already_kicked_off_fixture_is_excluded():
    m = _match(1, kickoff=NOW - timedelta(hours=1))
    assert select_fixtures_needing_social([m], NOW) == []


def test_fixture_without_kickoff_is_excluded():
    m = _match(1, kickoff=None)
    assert select_fixtures_needing_social([m], NOW) == []


def test_capped_and_sorted_by_nearest_kickoff():
    cap = settings.SOCIAL_MAX_FIXTURES_PER_RUN
    # cap + 3 fixtures, all in window, decreasing proximity by id.
    matches = [_match(i, kickoff=NOW + timedelta(hours=i)) for i in range(1, cap + 4)]
    result = select_fixtures_needing_social(matches, NOW)
    assert len(result) == cap
    assert result == list(range(1, cap + 1))  # nearest-kickoff first
