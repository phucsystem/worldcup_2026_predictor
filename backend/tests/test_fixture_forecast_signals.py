"""Tests for forecast_signals computation — no DB, no network.

Exercises _team_forecast_signals, _compute_forecast_signals, and the
FixtureDetail model field via pure mocked sessions.
"""
from unittest.mock import MagicMock

from app.api.fixtures import (
    ForecastSignals,
    ForecastSignalsSide,
    FixtureDetail,
    _compute_forecast_signals,
    _team_forecast_signals,
)


def _mock_session(matches: list[dict]):
    """Return a session-like object whose finished_group_matches_for_team
    call returns `matches` for any team."""
    session = MagicMock()
    # finished_group_matches_for_team is called by _team_forecast_signals
    # via the repository; patch the import at the fixtures module level.
    return session, matches


def _make_match(home, away, hs, as_, is_home_team_queried=None):
    return {
        "home_team": home,
        "away_team": away,
        "home_score": hs,
        "away_score": as_,
        "kickoff_utc": None,
        "events_json": None,
    }


# ---------------------------------------------------------------------------
# ForecastSignalsSide model
# ---------------------------------------------------------------------------

class TestForecastSignalsSideModel:
    def test_all_none_is_valid(self):
        side = ForecastSignalsSide()
        assert side.fifa_rank is None
        assert side.form is None
        assert side.goals_per_game is None

    def test_populated(self):
        side = ForecastSignalsSide(fifa_rank=5, form="WWDWL", goals_per_game=2.1)
        assert side.fifa_rank == 5
        assert side.form == "WWDWL"
        assert side.goals_per_game == 2.1


# ---------------------------------------------------------------------------
# _team_forecast_signals (via mocked finished_group_matches_for_team)
# ---------------------------------------------------------------------------

class TestTeamForecastSignals:
    def _patch_and_call(self, team: str, matches: list[dict]):
        """Patch repository.finished_group_matches_for_team on the fixtures
        module and call _team_forecast_signals."""
        import app.api.fixtures as fx_mod
        orig = fx_mod.finished_group_matches_for_team

        def fake_finished(session, t):
            return [m for m in matches if m["home_team"] == t or m["away_team"] == t]

        fx_mod.finished_group_matches_for_team = fake_finished
        try:
            result = _team_forecast_signals(MagicMock(), team)
        finally:
            fx_mod.finished_group_matches_for_team = orig
        return result

    def test_known_team_has_rank(self):
        side = self._patch_and_call("Brazil", [])
        assert side.fifa_rank == 5

    def test_unknown_team_rank_is_none(self):
        side = self._patch_and_call("Atlantis FC", [])
        assert side.fifa_rank is None

    def test_form_string_from_matches(self):
        matches = [
            _make_match("Brazil", "Serbia", 2, 0),
            _make_match("Germany", "Brazil", 0, 1),
            _make_match("Brazil", "Japan", 1, 1),
        ]
        side = self._patch_and_call("Brazil", matches)
        assert side.form == "WWD"

    def test_form_capped_at_5(self):
        matches = [
            _make_match("Brazil", "A", 1, 0),
            _make_match("Brazil", "B", 2, 0),
            _make_match("Brazil", "C", 3, 0),
            _make_match("Brazil", "D", 4, 0),
            _make_match("Brazil", "E", 5, 0),
            _make_match("Brazil", "F", 6, 0),
        ]
        side = self._patch_and_call("Brazil", matches)
        assert len(side.form) == 5

    def test_goals_per_game(self):
        matches = [
            _make_match("Brazil", "A", 3, 0),
            _make_match("B", "Brazil", 0, 2),
        ]
        side = self._patch_and_call("Brazil", matches)
        # 3 + 2 = 5 goals in 2 games → 2.5
        assert side.goals_per_game == 2.5

    def test_no_matches_form_and_gpg_none(self):
        side = self._patch_and_call("Spain", [])
        assert side.form is None
        assert side.goals_per_game is None


# ---------------------------------------------------------------------------
# _compute_forecast_signals
# ---------------------------------------------------------------------------

class TestComputeForecastSignals:
    def _patch_and_call(self, home, away, matches):
        import app.api.fixtures as fx_mod
        orig = fx_mod.finished_group_matches_for_team

        def fake_finished(session, t):
            return [m for m in matches if m["home_team"] == t or m["away_team"] == t]

        fx_mod.finished_group_matches_for_team = fake_finished
        try:
            result = _compute_forecast_signals(MagicMock(), home, away)
        finally:
            fx_mod.finished_group_matches_for_team = orig
        return result

    def test_returns_forecast_signals_for_known_teams(self):
        sig = self._patch_and_call("Brazil", "Japan", [])
        assert isinstance(sig, ForecastSignals)
        assert sig.home.fifa_rank == 5
        assert sig.away.fifa_rank == 16

    def test_omitted_when_both_unknown(self):
        sig = self._patch_and_call("Atlantis FC", "Utopia FC", [])
        assert sig is None

    def test_none_teams_returns_none(self):
        sig = self._patch_and_call(None, None, [])
        assert sig is None

    def test_one_side_unknown_still_returns_signals(self):
        # home is known (rank present), away is unknown — still meaningful
        sig = self._patch_and_call("Brazil", "Atlantis FC", [])
        assert sig is not None
        assert sig.home.fifa_rank == 5
        assert sig.away.fifa_rank is None


# ---------------------------------------------------------------------------
# FixtureDetail model carries forecast_signals
# ---------------------------------------------------------------------------

class TestFixtureDetailModel:
    def test_forecast_signals_optional_default_none(self):
        d = FixtureDetail(
            fixture_id=1, home_team="A", away_team="B",
            home_logo=None, away_logo=None,
        )
        assert d.forecast_signals is None

    def test_forecast_signals_populated(self):
        sig = ForecastSignals(
            home=ForecastSignalsSide(fifa_rank=5, form="WWW", goals_per_game=2.0),
            away=ForecastSignalsSide(fifa_rank=16, form="WDL", goals_per_game=1.2),
        )
        d = FixtureDetail(
            fixture_id=1, home_team="Brazil", away_team="Japan",
            home_logo=None, away_logo=None,
            forecast_signals=sig,
        )
        assert d.forecast_signals.home.fifa_rank == 5
        assert d.forecast_signals.away.form == "WDL"
