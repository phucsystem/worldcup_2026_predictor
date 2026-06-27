"""TDD tests for Slice 2: KO match forecast generation.

No DB, no network, no LLM — the builder is pure and the generator's client is
faked exactly as test_live_winprob_agent.py fakes make_structured_client.
"""
from contextlib import contextmanager

import app.data.collect as collect
from app.data.models import Match, StandingRow
from app.pipeline.forecast import (
    MatchForecast,
    ForecastFactor,
    build_ko_forecast_facts,
    generate_match_forecast,
)


HOME = "France"
AWAY = "Argentina"


def _row(team, group="A", position=1, points=9, won=3, drawn=0, lost=0,
         gf=7, ga=1, gd=6, qualification="qualified"):
    return StandingRow(
        group_name=group, team=team, position=position, points=points,
        played=3, won=won, drawn=drawn, lost=lost,
        gf=gf, ga=ga, gd=gd, qualification=qualification,
    )


class TestBuildKoForecastFacts:
    def test_returns_dict_with_both_teams_records(self):
        home_row = _row(HOME, group="A", position=1, points=9)
        away_row = _row(AWAY, group="B", position=2, points=6)
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=home_row, away_row=away_row,
        )
        assert facts is not None
        assert facts["home_team"] == HOME
        assert facts["away_team"] == AWAY
        assert facts["home_standings"]["points"] == 9
        assert facts["home_standings"]["position"] == 1
        assert facts["away_standings"]["points"] == 6
        assert facts["away_standings"]["position"] == 2

    def test_marked_as_knockout(self):
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=_row(AWAY),
        )
        assert facts["match_type"] == "knockout"
        assert "group_name" not in facts

    def test_carries_group_name_per_team(self):
        home_row = _row(HOME, group="Group A")
        away_row = _row(AWAY, group="Group B")
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=home_row, away_row=away_row,
        )
        assert facts["home_standings"]["team_group"] == "Group A"
        assert facts["away_standings"]["team_group"] == "Group B"

    def test_missing_home_row_yields_none(self):
        assert build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=None, away_row=_row(AWAY),
        ) is None

    def test_missing_away_row_yields_none(self):
        assert build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=None,
        ) is None

    def test_no_match_score_in_facts(self):
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=_row(AWAY),
        )
        assert "home_score" not in facts
        assert "away_score" not in facts


# ── Fake DeepSeek client (mirrors test_live_winprob_agent.py) ──────────────

class _FakeClient:
    def __init__(self, parsed=None, raise_exc=False):
        self._parsed = parsed
        self._raise = raise_exc
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        if self._raise:
            raise RuntimeError("deepseek boom")
        return {"parsed": self._parsed, "raw": None}


def _patch_client(monkeypatch, client):
    monkeypatch.setattr("app.llm.deepseek.make_structured_client", lambda schema: client)


def _good_forecast():
    return MatchForecast(
        home_pct=45, draw_pct=30, away_pct=25,
        factors=[
            ForecastFactor(name="Form", lean="home", why="France topped Group A on 9 points"),
        ],
    )


class TestGenerateKoMatchForecast:
    """generate_match_forecast with KO facts produces a valid normalized forecast."""

    def test_ko_facts_produce_valid_forecast(self, monkeypatch):
        client = _FakeClient(parsed=_good_forecast())
        _patch_client(monkeypatch, client)
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=_row(AWAY),
        )
        result = generate_match_forecast(facts, prompt_variant="ko")
        assert result is not None
        forecast, model = result
        assert forecast["home_pct"] + forecast["draw_pct"] + forecast["away_pct"] == 100
        assert all(v >= 0 for v in (forecast["home_pct"], forecast["draw_pct"], forecast["away_pct"]))
        assert len(forecast["factors"]) >= 1

    def test_ko_forecast_pcts_clamped_nonnegative(self, monkeypatch):
        parsed = MatchForecast(
            home_pct=-5, draw_pct=60, away_pct=45,
            factors=[ForecastFactor(name="X", lean="home", why="cited fact")],
        )
        client = _FakeClient(parsed=parsed)
        _patch_client(monkeypatch, client)
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=_row(AWAY),
        )
        result = generate_match_forecast(facts, prompt_variant="ko")
        assert result is not None
        forecast, _ = result
        assert forecast["home_pct"] >= 0
        assert forecast["home_pct"] + forecast["draw_pct"] + forecast["away_pct"] == 100

    def test_empty_factors_retries_and_returns_none(self, monkeypatch):
        parsed = MatchForecast(home_pct=50, draw_pct=30, away_pct=20, factors=[])
        client = _FakeClient(parsed=parsed)
        _patch_client(monkeypatch, client)
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=_row(AWAY),
        )
        result = generate_match_forecast(facts, prompt_variant="ko")
        assert result is None
        assert client.calls == 2  # retried twice

    def test_exception_returns_none(self, monkeypatch):
        client = _FakeClient(raise_exc=True)
        _patch_client(monkeypatch, client)
        facts = build_ko_forecast_facts(
            home_team=HOME, away_team=AWAY,
            home_row=_row(HOME), away_row=_row(AWAY),
        )
        assert generate_match_forecast(facts, prompt_variant="ko") is None


# ── backfill_forecasts integration (mocked DB + LLM) ──────────────────────

@contextmanager
def _fake_factory():
    yield object()


def _ko_match(fid, home="France", away="Argentina", stage="Round of 16"):
    return Match(
        fixture_id=fid, group_name=None,  # KO matches have no group_name
        home_team=home, away_team=away,
        home_score=None, away_score=None, status="NS", kickoff_utc=None,
        stage=stage,
    )


def _group_tables():
    """Minimal group_tables covering both KO teams."""
    return {
        "Group A": [_row("France", group="Group A", position=1, points=9)],
        "Group B": [_row("Argentina", group="Group B", position=2, points=6)],
    }


class TestBackfillForecastsKo:
    def test_ko_match_with_resolvable_rows_gets_forecast(self, monkeypatch):
        parsed = _good_forecast()

        monkeypatch.setattr("app.config.settings.DEEPSEEK_API_KEY", "k")
        monkeypatch.setattr("app.llm.deepseek.make_structured_client",
                            lambda schema: _FakeClient(parsed=parsed))
        stored = []
        monkeypatch.setattr(collect, "upsert_matches", lambda s, ms: stored.extend(ms))

        with monkeypatch.context() as m:
            # Patch the DB read to say no existing forecasts
            import sqlalchemy as sa
            class _FakeExec:
                def all(self):
                    return []
            class _FakeSession:
                def execute(self, _stmt):
                    return _FakeExec()
                def __enter__(self): return self
                def __exit__(self, *a): pass

            m.setattr(collect, "matches_table", collect.matches_table)

            count = collect.backfill_forecasts(
                lambda: _FakeSession(),
                [_ko_match(99)],
                _group_tables(),
            )

        assert count == 1
        assert stored[0].forecast_json is not None
        assert stored[0].forecast_kind == "ko"

    def test_ko_match_unresolvable_rows_skipped_no_crash(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.DEEPSEEK_API_KEY", "k")
        stored = []
        monkeypatch.setattr(collect, "upsert_matches", lambda s, ms: stored.extend(ms))

        class _FakeExec:
            def all(self):
                return []
        class _FakeSession:
            def execute(self, _stmt):
                return _FakeExec()
            def __enter__(self): return self
            def __exit__(self, *a): pass

        # group_tables has no entry for France or Argentina
        count = collect.backfill_forecasts(
            lambda: _FakeSession(),
            [_ko_match(99)],
            {},  # empty group_tables — can't resolve rows
        )
        assert count == 0
        assert stored == []

    def test_group_match_gets_forecast_kind_group(self, monkeypatch):
        parsed = _good_forecast()
        monkeypatch.setattr("app.config.settings.DEEPSEEK_API_KEY", "k")
        monkeypatch.setattr("app.llm.deepseek.make_structured_client",
                            lambda schema: _FakeClient(parsed=parsed))
        stored = []
        monkeypatch.setattr(collect, "upsert_matches", lambda s, ms: stored.extend(ms))

        group_match = Match(
            fixture_id=1, group_name="Group A",
            home_team="France", away_team="Germany",
            home_score=None, away_score=None, status="NS", kickoff_utc=None,
        )
        group_tables = {
            "Group A": [
                _row("France", group="Group A"),
                _row("Germany", group="Group A", position=2, points=6),
            ]
        }

        class _FakeExec:
            def all(self):
                return []
        class _FakeSession:
            def execute(self, _stmt):
                return _FakeExec()
            def __enter__(self): return self
            def __exit__(self, *a): pass

        count = collect.backfill_forecasts(
            lambda: _FakeSession(),
            [group_match],
            group_tables,
        )
        assert count == 1
        assert stored[0].forecast_kind == "group"

    def test_existing_forecast_skipped_unless_forced(self, monkeypatch):
        # A KO match that already has a stored forecast: skipped normally,
        # regenerated when its id is in force_ids (the "refresh upcoming" path).
        parsed = _good_forecast()
        monkeypatch.setattr("app.config.settings.DEEPSEEK_API_KEY", "k")
        monkeypatch.setattr("app.llm.deepseek.make_structured_client",
                            lambda schema: _FakeClient(parsed=parsed))
        stored = []
        monkeypatch.setattr(collect, "upsert_matches", lambda s, ms: stored.extend(ms))

        class _FakeExec:
            def all(self):
                return [(99, {"home_pct": 40, "draw_pct": 30, "away_pct": 30})]
        class _FakeSession:
            def execute(self, _stmt):
                return _FakeExec()
            def __enter__(self): return self
            def __exit__(self, *a): pass

        # Without force: existing forecast → skipped.
        count = collect.backfill_forecasts(
            lambda: _FakeSession(), [_ko_match(99)], _group_tables(),
        )
        assert count == 0 and stored == []

        # With force: regenerated despite existing forecast.
        count = collect.backfill_forecasts(
            lambda: _FakeSession(), [_ko_match(99)], _group_tables(), force_ids={99},
        )
        assert count == 1
        assert stored[0].forecast_kind == "ko"
