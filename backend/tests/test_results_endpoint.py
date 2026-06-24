"""Tests for GET /api/results and its pure shaper shape_results.

The shaper is the interesting part: it returns EVERY finished match with no
per-team cap (the whole point of the page — see app/api/standings recent_results
which caps at 5). The endpoint test only asserts the seed-independent route
contract, like the other endpoint tests.
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.results import shape_results
from app.main import app

client = TestClient(app)


def _dt(y, m, d, h=12):
    return datetime(y, m, d, h, 0, tzinfo=timezone.utc)


def _match(home, away, hs, as_, status="FT", kickoff=None, fixture_id=None,
           group_name="A", stage="Group Stage - 1", forecast=None):
    return {
        "fixture_id": fixture_id,
        "home_team": home,
        "away_team": away,
        "home_score": hs,
        "away_score": as_,
        "status": status,
        "kickoff_utc": kickoff,
        "group_name": group_name,
        "stage": stage,
        "forecast_json": forecast,
    }


def _fc(home_pct, draw_pct, away_pct):
    return {"home_pct": home_pct, "draw_pct": draw_pct, "away_pct": away_pct}


class TestShapeResults:
    def test_no_cap_keeps_every_match_for_a_team(self):
        # A finalist plays 8 games; the standings recent_results path would drop
        # the earliest 3. shape_results must keep all 8 so the page shows history
        # from the beginning.
        matches = [
            _match("Brazil", f"Opp{i}", 1, 0, kickoff=_dt(2026, 6, i + 1), fixture_id=i)
            for i in range(8)
        ]
        out = shape_results(matches)
        assert len(out) == 8

    def test_newest_first(self):
        matches = [
            _match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12), fixture_id=1),
            _match("France", "Poland", 0, 2, kickoff=_dt(2026, 6, 20), fixture_id=2),
            _match("Spain", "Italy", 1, 1, kickoff=_dt(2026, 6, 15), fixture_id=3),
        ]
        assert [r.fixture_id for r in shape_results(matches)] == [2, 3, 1]

    def test_excludes_inplay_notstarted_and_scoreless(self):
        matches = [
            _match("Brazil", "Serbia", 3, 1, status="FT", kickoff=_dt(2026, 6, 12)),
            _match("Brazil", "Spain", 0, 0, status="1H", kickoff=_dt(2026, 6, 15)),
            _match("Brazil", "France", None, None, status="NS", kickoff=_dt(2026, 6, 18)),
            _match("Brazil", "Italy", None, None, status="FT", kickoff=_dt(2026, 6, 16)),
        ]
        out = shape_results(matches)
        assert len(out) == 1
        assert out[0].away_team == "Serbia"

    def test_includes_aet_and_pen(self):
        matches = [
            _match("Brazil", "Serbia", 2, 2, status="PEN", kickoff=_dt(2026, 7, 1),
                   group_name=None, stage="Final"),
            _match("Brazil", "Spain", 1, 0, status="AET", kickoff=_dt(2026, 7, 5),
                   group_name=None, stage="Semi-finals"),
        ]
        assert len(shape_results(matches)) == 2

    def test_knockout_carries_stage_and_null_group(self):
        out = shape_results([
            _match("Brazil", "Serbia", 2, 1, kickoff=_dt(2026, 7, 1),
                   group_name=None, stage="Round of 16"),
        ])
        assert out[0].group_name is None
        assert out[0].stage == "Round of 16"

    def test_forecast_correct_present_for_group_stage(self):
        out = shape_results([
            _match("Brazil", "Serbia", 3, 1, kickoff=_dt(2026, 6, 12), forecast=_fc(60, 25, 15)),
        ])
        assert out[0].forecast_correct is True

    def test_forecast_correct_none_for_knockout_without_forecast(self):
        out = shape_results([
            _match("Brazil", "Serbia", 2, 1, kickoff=_dt(2026, 7, 1),
                   group_name=None, stage="Round of 16", forecast=None),
        ])
        assert out[0].forecast_correct is None

    def test_empty_input_returns_empty(self):
        assert shape_results([]) == []


class TestResultsEndpoint:
    def test_returns_200_and_a_list(self):
        resp = client.get("/api/results")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
