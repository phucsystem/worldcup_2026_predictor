"""Unit tests for API-Football payload mapping — no network.

Covers the live-match fields (elapsed minute) and the `?live=all` query param
used by the lightweight live poller.
"""

from app.data.api_football import APIFootballClient, _map_fixture


def _raw(short: str, elapsed, home_goals, away_goals):
    return {
        "fixture": {
            "id": 42,
            "date": "2026-06-19T18:00:00+00:00",
            "status": {"short": short, "elapsed": elapsed},
        },
        "teams": {"home": {"name": "Switzerland"}, "away": {"name": "Cameroon"}},
        "goals": {"home": home_goals, "away": away_goals},
        "league": {"round": "Group Stage - 3"},
    }


class TestMapFixtureElapsed:
    def test_in_play_carries_elapsed_and_score(self):
        m = _map_fixture(_raw("2H", 67, 1, 0))
        assert m.elapsed == 67
        assert m.home_score == 1
        assert m.away_score == 0
        assert m.status == "2H"

    def test_missing_elapsed_is_none(self):
        m = _map_fixture(_raw("NS", None, None, None))
        assert m.elapsed is None

    def test_half_time_keeps_elapsed(self):
        m = _map_fixture(_raw("HT", 45, 0, 0))
        assert m.elapsed == 45
        assert m.status == "HT"


def _raw_ko(short, home_goals, away_goals, *, score=None, home_winner=None, away_winner=None):
    raw = {
        "fixture": {
            "id": 99,
            "date": "2026-07-05T18:00:00+00:00",
            "status": {"short": short, "elapsed": None},
        },
        "teams": {
            "home": {"name": "Brazil", "winner": home_winner},
            "away": {"name": "Argentina", "winner": away_winner},
        },
        "goals": {"home": home_goals, "away": away_goals},
        "league": {"round": "Round of 16"},
    }
    if score is not None:
        raw["score"] = score
    return raw


class TestMapFixtureKnockoutResult:
    def test_ft_home_win_sets_winner_side_from_flag(self):
        m = _map_fixture(_raw_ko("FT", 2, 1, home_winner=True, away_winner=False))
        assert m.winner_side == "home"
        assert m.home_pen is None and m.away_pen is None

    def test_aet_away_win(self):
        score = {"penalty": {"home": None, "away": None}}
        m = _map_fixture(_raw_ko("AET", 1, 2, score=score, home_winner=False, away_winner=True))
        assert m.winner_side == "away"
        assert m.home_pen is None and m.away_pen is None

    def test_pen_win_captures_shootout_and_winner(self):
        # 1-1 after ET, away advance 4-3 on penalties.
        score = {"penalty": {"home": 3, "away": 4}}
        m = _map_fixture(_raw_ko("PEN", 1, 1, score=score, home_winner=False, away_winner=True))
        assert m.home_score == 1 and m.away_score == 1
        assert m.home_pen == 3 and m.away_pen == 4
        assert m.winner_side == "away"

    def test_undecided_leaves_all_none(self):
        m = _map_fixture(_raw_ko("NS", None, None))
        assert m.winner_side is None
        assert m.home_pen is None and m.away_pen is None


class TestGetFixturesLiveParam:
    def test_live_true_sends_live_all(self):
        client = APIFootballClient()
        captured = {}

        def fake_get(path, params):
            captured["path"] = path
            captured["params"] = params
            return {"response": []}

        client._get = fake_get  # type: ignore[method-assign]
        client.get_fixtures(live=True)
        assert captured["params"].get("live") == "all"

    def test_default_omits_live(self):
        client = APIFootballClient()
        captured = {}

        def fake_get(path, params):
            captured["params"] = params
            return {"response": []}

        client._get = fake_get  # type: ignore[method-assign]
        client.get_fixtures()
        assert "live" not in captured["params"]
