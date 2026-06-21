"""Unit tests for match-event normalization + backfill selection — no DB, no network."""

from app.api.fixtures import (
    MatchEvent,
    normalize_events,
    select_fixtures_needing_events,
)
from app.data.models import Match


def _raw(elapsed, type_, detail, team, player=None, assist=None, extra=None):
    return {
        "time": {"elapsed": elapsed, "extra": extra},
        "team": {"name": team},
        "player": {"name": player},
        "assist": {"name": assist},
        "type": type_,
        "detail": detail,
    }


HOME = "France"
AWAY = "Brazil"


# ---------------------------------------------------------------------------
# normalize_events
# ---------------------------------------------------------------------------

class TestNormalizeEvents:
    def test_goal_maps_to_home_side(self):
        out = normalize_events(
            [_raw(23, "Goal", "Normal Goal", HOME, player="Mbappé")], HOME, AWAY
        )
        assert out == [
            MatchEvent(
                minute=23, extra=None, type="Goal", detail="Normal Goal",
                player="Mbappé", assist=None, team=HOME, side="home",
            )
        ]

    def test_away_goal_with_assist(self):
        out = normalize_events(
            [_raw(67, "Goal", "Normal Goal", AWAY, player="Vinicius", assist="Neymar")],
            HOME, AWAY,
        )
        assert out[0].side == "away"
        assert out[0].assist == "Neymar"

    def test_card_event(self):
        out = normalize_events(
            [_raw(40, "Card", "Yellow Card", HOME, player="Rabiot")], HOME, AWAY
        )
        assert out[0].type == "Card"
        assert out[0].detail == "Yellow Card"
        assert out[0].side == "home"

    def test_substitution_event(self):
        out = normalize_events(
            [_raw(70, "subst", "Substitution 1", AWAY, player="In", assist="Out")],
            HOME, AWAY,
        )
        assert out[0].type == "subst"
        assert out[0].side == "away"

    def test_unknown_team_side_is_none(self):
        out = normalize_events(
            [_raw(10, "Goal", "Normal Goal", "Mars", player="Alien")], HOME, AWAY
        )
        assert out[0].side is None
        assert out[0].team == "Mars"

    def test_extra_time_minute(self):
        out = normalize_events(
            [_raw(90, "Goal", "Normal Goal", HOME, player="Giroud", extra=3)], HOME, AWAY
        )
        assert out[0].minute == 90
        assert out[0].extra == 3

    def test_empty_and_none_input(self):
        assert normalize_events([], HOME, AWAY) == []
        assert normalize_events(None, HOME, AWAY) == []


# ---------------------------------------------------------------------------
# select_fixtures_needing_events
# ---------------------------------------------------------------------------

def _match(fid, status):
    return Match(
        fixture_id=fid, group_name=None, home_team=HOME, away_team=AWAY,
        home_score=None, away_score=None, status=status, kickoff_utc=None,
    )


class TestSelectFixturesNeedingEvents:
    def test_finished_without_events_is_selected(self):
        matches = [_match(1, "FT")]
        assert select_fixtures_needing_events(matches, existing=set()) == [1]

    def test_finished_with_events_is_skipped(self):
        matches = [_match(1, "FT")]
        assert select_fixtures_needing_events(matches, existing={1}) == []

    def test_not_started_is_skipped(self):
        matches = [_match(1, "NS")]
        assert select_fixtures_needing_events(matches, existing=set()) == []

    def test_live_is_skipped(self):
        # in-play matches are handled by the live poller, not the daily backfill
        matches = [_match(1, "2H")]
        assert select_fixtures_needing_events(matches, existing=set()) == []

    def test_aet_and_pen_are_finished(self):
        matches = [_match(1, "AET"), _match(2, "PEN")]
        assert select_fixtures_needing_events(matches, existing=set()) == [1, 2]

    def test_mixed_set(self):
        matches = [_match(1, "FT"), _match(2, "NS"), _match(3, "FT"), _match(4, "FT")]
        assert select_fixtures_needing_events(matches, existing={3}) == [1, 4]
