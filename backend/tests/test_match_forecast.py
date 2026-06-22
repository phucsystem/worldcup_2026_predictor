"""Unit tests for the forecast fact-bundle builder, percentage normalization,
and backfill selection.

No DB, no network, no LLM — the builder is pure and is the ONLY thing handed to
DeepSeek, so the grounding guard is exercised directly. The percentages a model
returns are normalized deterministically here.
"""

from app.api.fixtures import select_fixtures_needing_forecast
from app.data.models import Match, StandingRow
from app.pipeline.forecast import _normalize_pcts, build_match_forecast_facts

HOME = "Brazil"
AWAY = "Serbia"


def _rows():
    return [
        StandingRow(group_name="G", team="Brazil", points=9, position=1, gd=6, qualification="qualified"),
        StandingRow(group_name="G", team="Serbia", points=3, position=3, gd=-2, qualification="contention"),
    ]


class TestBuildForecastFacts:
    def _facts(self, rows):
        home_row = next((r for r in rows if r.team == HOME), None)
        away_row = next((r for r in rows if r.team == AWAY), None)
        return build_match_forecast_facts(
            home_team=HOME, away_team=AWAY, home_row=home_row, away_row=away_row, group_name="G",
        )

    def test_projects_both_teams_standings(self):
        f = self._facts(_rows())
        assert f["home_team"] == "Brazil" and f["away_team"] == "Serbia"
        assert f["home_standings"]["points"] == 9
        assert f["home_standings"]["position"] == 1
        assert f["away_standings"]["goal_difference"] == -2
        assert f["away_standings"]["qualification"] == "contention"

    def test_missing_home_row_yields_none(self):
        # Only Serbia has a row — nothing to ground the home side on.
        f = self._facts([_rows()[1]])
        assert f is None

    def test_missing_away_row_yields_none(self):
        f = self._facts([_rows()[0]])
        assert f is None

    def test_no_rows_yields_none(self):
        assert self._facts([]) is None

    def test_carries_no_match_score(self):
        # The bundle must not leak this fixture's own result into the forecast.
        f = self._facts(_rows())
        assert "home_score" not in f and "away_score" not in f and "result" not in f


class TestNormalizePcts:
    def test_already_summing_to_100_unchanged(self):
        assert _normalize_pcts(58, 24, 18) == (58, 24, 18)

    def test_rescales_to_100(self):
        assert sum(_normalize_pcts(50, 30, 30)) == 100

    def test_remainder_absorbed_by_largest(self):
        h, d, a = _normalize_pcts(33, 33, 33)
        assert (h, d, a) == (34, 33, 33)
        assert h + d + a == 100

    def test_negatives_clamped(self):
        h, d, a = _normalize_pcts(-10, 60, 50)
        assert h == 0 and h + d + a == 100

    def test_all_zero_falls_back(self):
        assert _normalize_pcts(0, 0, 0) == (34, 33, 33)


def _match(fid, group_name):
    return Match(
        fixture_id=fid, group_name=group_name, home_team=HOME, away_team=AWAY,
        home_score=None, away_score=None, status="NS", kickoff_utc=None,
    )


class TestSelectFixturesNeedingForecast:
    def test_group_match_without_forecast_is_selected(self):
        assert select_fixtures_needing_forecast([_match(1, "G")], existing=set()) == [1]

    def test_group_match_with_forecast_is_skipped(self):
        assert select_fixtures_needing_forecast([_match(1, "G")], existing={1}) == []

    def test_knockout_match_without_group_is_skipped(self):
        assert select_fixtures_needing_forecast([_match(1, None)], existing=set()) == []
