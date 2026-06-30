"""
Unit tests for recent-form shaping in app.api.standings — no DB, no network.
Covers match_outcome (pure W/D/L) and recent_results_by_team (strict finished
filter, most-recent ordering, per-team cap, graceful degrade).
"""

from datetime import datetime, timezone

from app.api.standings import (
    forecast_correct,
    match_outcome,
    recent_results_by_team,
)


def _dt(y, m, d, h=12):
    return datetime(y, m, d, h, 0, tzinfo=timezone.utc)


def _match(home, away, hs, as_, status="FT", kickoff=None, fixture_id=None, forecast=None,
           winner_side=None, home_pen=None, away_pen=None):
    return {
        "fixture_id": fixture_id,
        "home_team": home,
        "away_team": away,
        "home_score": hs,
        "away_score": as_,
        "status": status,
        "winner_side": winner_side,
        "home_pen": home_pen,
        "away_pen": away_pen,
        "kickoff_utc": kickoff,
        "forecast_json": forecast,
    }


def _fc(home_pct, draw_pct, away_pct):
    return {"home_pct": home_pct, "draw_pct": draw_pct, "away_pct": away_pct}


# ---------------------------------------------------------------------------
# match_outcome (pure)
# ---------------------------------------------------------------------------

class TestMatchOutcome:
    def test_home_win(self):
        m = _match("Brazil", "Serbia", 3, 1)
        assert match_outcome("Brazil", m) == "W"
        assert match_outcome("Serbia", m) == "L"

    def test_away_win(self):
        m = _match("Brazil", "Serbia", 0, 2)
        assert match_outcome("Brazil", m) == "L"
        assert match_outcome("Serbia", m) == "W"

    def test_draw_from_both_sides(self):
        m = _match("Brazil", "Serbia", 1, 1)
        assert match_outcome("Brazil", m) == "D"
        assert match_outcome("Serbia", m) == "D"

    def test_penalty_win_prefers_winner_side_over_level_score(self):
        # 1-1 after extra time; away advance on penalties → W/L, not D/D.
        m = _match("Brazil", "Serbia", 1, 1, status="PEN", winner_side="away",
                   home_pen=3, away_pen=4)
        assert match_outcome("Serbia", m) == "W"
        assert match_outcome("Brazil", m) == "L"


# ---------------------------------------------------------------------------
# recent_results_by_team
# ---------------------------------------------------------------------------

class TestRecentResultsByTeam:
    def test_strict_finished_filter_excludes_inplay_and_notstarted(self):
        matches = [
            _match("Brazil", "Serbia", 3, 1, status="FT", kickoff=_dt(2026, 6, 12)),
            _match("Brazil", "Spain", 0, 0, status="1H", kickoff=_dt(2026, 6, 15)),
            _match("Brazil", "France", None, None, status="NS", kickoff=_dt(2026, 6, 18)),
            _match("Brazil", "Italy", 1, 0, status="HT", kickoff=_dt(2026, 6, 16)),
        ]
        out = recent_results_by_team(matches)
        assert [r.outcome for r in out["Brazil"]] == ["W"]
        assert len(out["Brazil"]) == 1

    def test_includes_aet_and_pen(self):
        matches = [
            _match("Brazil", "Serbia", 2, 2, status="PEN", kickoff=_dt(2026, 7, 1)),
            _match("Brazil", "Spain", 1, 0, status="AET", kickoff=_dt(2026, 7, 5)),
        ]
        out = recent_results_by_team(matches)
        assert len(out["Brazil"]) == 2

    def test_most_recent_first(self):
        matches = [
            _match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12)),
            _match("Brazil", "Spain", 0, 2, kickoff=_dt(2026, 6, 18)),
            _match("Brazil", "Italy", 1, 1, kickoff=_dt(2026, 6, 15)),
        ]
        out = recent_results_by_team(matches)
        # most-recent (Jun 18) first → L, then Jun 15 D, then Jun 12 W
        assert [r.outcome for r in out["Brazil"]] == ["L", "D", "W"]

    def test_caps_at_five(self):
        matches = [
            _match("Brazil", f"Opp{i}", 1, 0, kickoff=_dt(2026, 6, i + 1))
            for i in range(8)
        ]
        out = recent_results_by_team(matches)
        assert len(out["Brazil"]) == 5
        # newest kept (Jun 8 = i7), oldest (Jun 1..3) dropped
        assert out["Brazil"][0].away_team == "Opp7"

    def test_zero_finished_returns_empty_map(self):
        matches = [
            _match("Brazil", "Spain", None, None, status="NS", kickoff=_dt(2026, 6, 18)),
        ]
        out = recent_results_by_team(matches)
        assert out == {}

    def test_unknown_team_absent(self):
        matches = [_match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12))]
        out = recent_results_by_team(matches)
        assert "Argentina" not in out

    def test_match_attaches_to_both_teams(self):
        matches = [_match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12))]
        out = recent_results_by_team(matches)
        assert out["Brazil"][0].outcome == "W"
        assert out["Serbia"][0].outcome == "L"
        # full scoreline preserved on both
        assert out["Serbia"][0].home_team == "Brazil"
        assert out["Serbia"][0].home_score == 3

    def test_missing_scores_with_finished_status_excluded(self):
        # a "finished" status but null scores must not crash or count
        matches = [_match("Brazil", "Serbia", None, None, status="FT", kickoff=_dt(2026, 6, 12))]
        out = recent_results_by_team(matches)
        assert out == {}

    def test_fixture_id_carried_for_both_teams(self):
        # the result row must carry its fixture_id so the UI can link to /match/{id}
        matches = [_match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12), fixture_id=42)]
        out = recent_results_by_team(matches)
        assert out["Brazil"][0].fixture_id == 42
        assert out["Serbia"][0].fixture_id == 42

    def test_fixture_id_defaults_none_when_absent(self):
        matches = [{
            "home_team": "Brazil", "away_team": "Serbia", "home_score": 3,
            "away_score": 1, "status": "FT", "kickoff_utc": _dt(2026, 6, 12),
        }]
        out = recent_results_by_team(matches)
        assert out["Brazil"][0].fixture_id is None

    def test_forecast_correct_carried_for_both_teams(self):
        # home favoured, home won → correct from both team perspectives
        matches = [
            _match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12), forecast=_fc(60, 25, 15)),
        ]
        out = recent_results_by_team(matches)
        assert out["Brazil"][0].forecast_correct is True
        assert out["Serbia"][0].forecast_correct is True

    def test_forecast_correct_none_without_forecast(self):
        matches = [_match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12))]
        out = recent_results_by_team(matches)
        assert out["Brazil"][0].forecast_correct is None


# ---------------------------------------------------------------------------
# forecast_correct (pure)
# ---------------------------------------------------------------------------

class TestForecastCorrect:
    def test_home_favoured_and_home_won(self):
        assert forecast_correct(_fc(60, 25, 15), 2, 0) is True

    def test_home_favoured_but_draw(self):
        assert forecast_correct(_fc(60, 25, 15), 1, 1) is False

    def test_away_favoured_and_away_won(self):
        assert forecast_correct(_fc(20, 30, 50), 0, 2) is True

    def test_draw_favoured_and_draw(self):
        assert forecast_correct(_fc(25, 50, 25), 1, 1) is True

    def test_none_when_no_forecast(self):
        assert forecast_correct(None, 2, 0) is None

    def test_none_when_scores_missing(self):
        assert forecast_correct(_fc(60, 25, 15), None, None) is None

    def test_none_when_pct_missing(self):
        assert forecast_correct({"home_pct": 60}, 2, 0) is None

    def test_tie_in_pct_prefers_home_then_away(self):
        # home_pct ties draw/away at the top → predicts home
        assert forecast_correct(_fc(40, 40, 20), 2, 0) is True
