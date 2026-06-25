"""Unit tests for the live win-prob agent: the pure fact builder, the keep-last-good
generator (DeepSeek mocked), and the Python-side bound enforcement cross-check.

No DB, no network — the builder is the fabrication-guard exercised directly, and the
generator's client is faked the way the intelligence tests fake make_structured_client.
"""

import pytest

from app.api.fixtures import MatchEvent
from app.pipeline.live_winprob_agent import (
    LIVE_AGENT_MODEL,
    LiveWinProbAgent,
    WinProbAdjustment,
    build_agent_facts,
    generate_live_winprob,
)
from app.pipeline.winprob import ADJ_BAND, apply_adjustment

BASE = {"home": 55, "draw": 25, "away": 20}


def _goal(minute, side, player):
    team = "Brazil" if side == "home" else "Serbia"
    return MatchEvent(minute=minute, type="Goal", detail="Normal Goal",
                      player=player, side=side, team=team)


def _red(minute, side):
    team = "Brazil" if side == "home" else "Serbia"
    return MatchEvent(minute=minute, type="Card", detail="Red Card", player="D",
                      side=side, team=team)


class TestBuildAgentFacts:
    def test_includes_base_signals_scorers_cards(self):
        facts = build_agent_facts(
            home_team="Brazil", away_team="Serbia", home_score=1, away_score=0,
            minute=60, status="2H", base=BASE,
            signals={"xg_diff": 1.2, "possession_diff": 18},
            events=[_goal(30, "home", "Vinícius Jr"), _red(55, "away")],
            qualification={"home": "qualified"},
        )
        assert facts["base_win_probability"] == BASE
        assert facts["signals"]["xg_diff"] == 1.2
        assert facts["scorers"][0]["player"] == "Vinícius Jr"
        assert facts["red_cards"][0]["team"] == "Serbia"
        assert facts["qualification"] == {"home": "qualified"}

    def test_omits_absent_signals_and_qualification(self):
        facts = build_agent_facts(
            home_team="Brazil", away_team="Serbia", home_score=0, away_score=0,
            minute=10, status="1H", base=BASE, signals={}, events=[],
            qualification=None,
        )
        assert facts["signals"] == {}
        assert facts["scorers"] == []
        assert facts["red_cards"] == []
        assert "qualification" not in facts

    def test_never_includes_a_final_result(self):
        facts = build_agent_facts(
            home_team="Brazil", away_team="Serbia", home_score=2, away_score=0,
            minute=80, status="2H", base=BASE, signals={}, events=[],
        )
        assert "result" not in facts
        assert "winner" not in facts
        assert facts["status"] == "2H"


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


class TestGenerateLiveWinProb:
    def test_returns_payload_and_model(self, monkeypatch):
        parsed = LiveWinProbAgent(
            adjustment=WinProbAdjustment(home=6, draw=-3, away=-3),
            read="Brazil are pressing and lead through an early goal.",
        )
        client = _FakeClient(parsed=parsed)
        _patch_client(monkeypatch, client)
        result = generate_live_winprob({"any": "facts"})
        assert result is not None
        payload, model = result
        assert model == LIVE_AGENT_MODEL
        assert payload["adjustment"] == {"home": 6, "draw": -3, "away": -3}
        assert payload["read"].startswith("Brazil are pressing")

    def test_empty_read_yields_none_after_retries(self, monkeypatch):
        parsed = LiveWinProbAgent(
            adjustment=WinProbAdjustment(home=0, draw=0, away=0), read="   ",
        )
        client = _FakeClient(parsed=parsed)
        _patch_client(monkeypatch, client)
        assert generate_live_winprob({"f": 1}) is None
        assert client.calls == 2  # retried twice

    def test_exception_yields_none(self, monkeypatch):
        client = _FakeClient(raise_exc=True)
        _patch_client(monkeypatch, client)
        assert generate_live_winprob({"f": 1}) is None


class TestBoundEnforcementCrossCheck:
    def test_oversized_agent_adjustment_clamped_by_apply_adjustment(self):
        # A wild adjustment from the model, once routed through apply_adjustment,
        # can never move the final more than ADJ_BAND from the base per outcome.
        wild = {"home": 40, "draw": -40, "away": 0}
        final = apply_adjustment(BASE, wild)
        assert final["home"] - BASE["home"] <= ADJ_BAND
        assert BASE["draw"] - final["draw"] <= ADJ_BAND
        assert sum(final.values()) == 100
