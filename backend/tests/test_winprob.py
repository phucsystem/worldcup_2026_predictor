"""Unit tests for the pure live win-probability module (no DB / network / LLM).

`compute_base` is a time-decayed Poisson/Skellam over the remaining goals;
`extract_signals` is a deterministic context bundle for the Phase-3 agent; and
`apply_adjustment` clamps the agent's per-outcome delta to base ±ADJ_BAND and
re-normalizes, keeping the calibrated base authoritative.
"""

from app.api.fixtures import MatchEvent
from app.data.models import StandingRow
from app.pipeline.winprob import (
    ADJ_BAND,
    REFRESH_MINUTES,
    apply_adjustment,
    compute_base,
    extract_signals,
    live_read_signature,
)


def _pct_sum(d):
    return d["home"] + d["draw"] + d["away"]


class TestComputeBaseShape:
    def test_sums_to_100_across_grid(self):
        for hs, as_ in [(0, 0), (1, 0), (0, 2), (2, 2), (3, 1)]:
            for minute in [1, 25, 45, 70, 90, 95, 120]:
                base = compute_base(hs, as_, minute)
                assert _pct_sum(base) == 100, (hs, as_, minute, base)
                assert all(v >= 0 for v in base.values())

    def test_goalless_early_is_near_even_with_draw_share(self):
        base = compute_base(0, 0, 1)
        # Not collapsed onto any single outcome.
        assert base != {"home": 100, "draw": 0, "away": 0}
        assert base["draw"] > 0
        # Symmetric with no prior.
        assert abs(base["home"] - base["away"]) <= 1


class TestComputeBaseEndState:
    def test_two_nil_at_90_is_high_but_not_certain(self):
        base = compute_base(2, 0, 90)
        assert base["home"] >= 90
        assert base["home"] < 100  # a sliver remains under the 95' anchor

    def test_two_nil_at_full_time_collapses_to_scoreline(self):
        base = compute_base(2, 0, 95)
        assert base == {"home": 100, "draw": 0, "away": 0}
        # Beyond 95' (ET/PENS treated as decided) stays collapsed.
        assert compute_base(2, 0, 120) == {"home": 100, "draw": 0, "away": 0}

    def test_level_at_full_time_collapses_to_draw(self):
        assert compute_base(1, 1, 95) == {"home": 0, "draw": 100, "away": 0}

    def test_level_late_draw_dominant(self):
        base = compute_base(1, 1, 89)
        assert base["draw"] > base["home"]
        assert base["draw"] > base["away"]


class TestComputeBaseDynamics:
    def test_leader_probability_increases_with_minute(self):
        # Fixed 1-0 lead: P(leader) is monotone non-decreasing as time runs down.
        seq = [compute_base(1, 0, m)["home"] for m in [20, 45, 70, 88]]
        assert seq == sorted(seq)
        assert seq[-1] > seq[0]

    def test_prior_tilts_home_but_weakly(self):
        strong_home = {"home_pct": 70, "draw_pct": 15, "away_pct": 15}
        tilted = compute_base(0, 0, 10, prior=strong_home)
        even = compute_base(0, 0, 10)
        assert tilted["home"] > tilted["away"]
        assert tilted["home"] > even["home"]
        # Weak: the live game-state keeps it from mirroring the 70/15 prior.
        assert tilted["home"] < 70

    def test_red_card_shifts_toward_opponent(self):
        with_red = compute_base(0, 0, 30, away_red=1)
        without = compute_base(0, 0, 30)
        assert with_red["home"] > without["home"]

    def test_symmetry_under_score_and_prior_swap(self):
        prior = {"home_pct": 60, "draw_pct": 20, "away_pct": 20}
        swapped_prior = {"home_pct": 20, "draw_pct": 20, "away_pct": 60}
        a = compute_base(2, 1, 60, prior=prior, home_red=1)
        b = compute_base(1, 2, 60, prior=swapped_prior, away_red=1)
        assert a["home"] == b["away"]
        assert a["away"] == b["home"]
        assert a["draw"] == b["draw"]


class TestApplyAdjustment:
    def test_none_delta_is_identity(self):
        base = {"home": 50, "draw": 30, "away": 20}
        assert apply_adjustment(base, None) == base

    def test_zero_delta_is_identity(self):
        base = {"home": 50, "draw": 30, "away": 20}
        assert apply_adjustment(base, {"home": 0, "draw": 0, "away": 0}) == base

    def test_in_band_delta_applied(self):
        base = {"home": 50, "draw": 30, "away": 20}
        out = apply_adjustment(base, {"home": 6, "draw": -3, "away": -3})
        assert _pct_sum(out) == 100
        assert out["home"] == 56

    def test_oversized_delta_clamped_to_band(self):
        base = {"home": 40, "draw": 30, "away": 30}
        # A wild +50/-50 split is clamped to base ±ADJ_BAND before normalizing.
        out = apply_adjustment(base, {"home": 50, "draw": -50, "away": 0})
        assert _pct_sum(out) == 100
        assert out["home"] - base["home"] <= ADJ_BAND
        assert base["draw"] - out["draw"] <= ADJ_BAND

    def test_one_sided_delta_renormalizes(self):
        base = {"home": 34, "draw": 33, "away": 33}
        out = apply_adjustment(base, {"home": 8, "draw": -4, "away": -4})
        assert _pct_sum(out) == 100
        assert out["home"] > base["home"]

    def test_non_zero_sum_delta_still_respects_band(self):
        # A delta whose components are each within the band but do NOT sum to zero
        # must still never move any outcome more than the band from the base.
        base = {"home": 65, "draw": 21, "away": 14}
        out = apply_adjustment(base, {"home": -6, "draw": -10, "away": -10})
        assert _pct_sum(out) == 100
        for k in ("home", "draw", "away"):
            assert abs(out[k] - base[k]) <= ADJ_BAND, (k, out, base)

    def test_band_invariant_holds_across_grid(self):
        from itertools import product

        bases = [
            {"home": 34, "draw": 33, "away": 33},
            {"home": 65, "draw": 21, "away": 14},
            {"home": 4, "draw": 6, "away": 90},
            {"home": 50, "draw": 8, "away": 42},
        ]
        steps = range(-20, 21, 5)
        for base in bases:
            for dh, dd, da in product(steps, steps, steps):
                out = apply_adjustment(base, {"home": dh, "draw": dd, "away": da})
                assert _pct_sum(out) == 100, (base, dh, dd, da, out)
                for k in ("home", "draw", "away"):
                    assert out[k] >= 0
                    assert abs(out[k] - base[k]) <= ADJ_BAND, (k, base, (dh, dd, da), out)


class TestExtractSignals:
    def _stats(self):
        return [
            {
                "team": {"name": "Brazil"},
                "statistics": [
                    {"type": "expected_goals", "value": "1.80"},
                    {"type": "Shots on Goal", "value": 6},
                    {"type": "Ball Possession", "value": "60%"},
                ],
            },
            {
                "team": {"name": "Serbia"},
                "statistics": [
                    {"type": "expected_goals", "value": "0.50"},
                    {"type": "Shots on Goal", "value": 2},
                    {"type": "Ball Possession", "value": "40%"},
                ],
            },
        ]

    def _rows(self):
        return (
            StandingRow(group_name="G", team="Brazil", won=2, drawn=0, lost=0,
                        points=6, position=1, qualification="qualified"),
            StandingRow(group_name="G", team="Serbia", won=0, drawn=1, lost=1,
                        points=1, position=4, qualification="contention"),
        )

    def test_present_stats_yield_diffs(self):
        home_row, away_row = self._rows()
        sig = extract_signals(
            statistics=self._stats(),
            events=[],
            home_team="Brazil",
            away_team="Serbia",
            home_row=home_row,
            away_row=away_row,
        )
        assert sig["xg_diff"] == 1.3
        assert sig["shots_on_diff"] == 4
        assert sig["possession_diff"] == 20

    def test_absent_stats_omitted_not_zero_filled(self):
        sig = extract_signals(
            statistics=None,
            events=[],
            home_team="Brazil",
            away_team="Serbia",
            home_row=None,
            away_row=None,
        )
        assert "xg_diff" not in sig
        assert "shots_on_diff" not in sig
        assert "possession_diff" not in sig
        assert "form" not in sig

    def test_red_cards_counted_from_events(self):
        events = [
            MatchEvent(minute=30, type="Card", detail="Red Card", player="X",
                       side="home", team="Brazil"),
            MatchEvent(minute=40, type="Card", detail="Yellow Card", player="Y",
                       side="away", team="Serbia"),
        ]
        sig = extract_signals(
            statistics=None, events=events,
            home_team="Brazil", away_team="Serbia",
            home_row=None, away_row=None,
        )
        assert sig["home_red"] == 1
        assert sig.get("away_red", 0) == 0

    def test_standings_rows_yield_form_and_qualification(self):
        home_row, away_row = self._rows()
        sig = extract_signals(
            statistics=None, events=[],
            home_team="Brazil", away_team="Serbia",
            home_row=home_row, away_row=away_row,
        )
        assert sig["form"]["home"] == {"won": 2, "drawn": 0, "lost": 0}
        assert sig["qualification"]["away"] == "contention"


class TestLiveReadSignature:
    def _goal(self, minute):
        return MatchEvent(minute=minute, type="Goal", detail="Normal Goal",
                          player="X", side="home", team="Brazil")

    def _red(self, minute):
        return MatchEvent(minute=minute, type="Card", detail="Red Card",
                          player="Y", side="away", team="Serbia")

    def _yellow(self, minute):
        return MatchEvent(minute=minute, type="Card", detail="Yellow Card",
                          player="Z", side="home", team="Brazil")

    def test_identical_inputs_same_sig(self):
        events = [self._goal(10)]
        assert live_read_signature(events, "1H", 20) == live_read_signature(events, "1H", 20)

    def test_new_goal_changes_sig(self):
        before = live_read_signature([self._goal(10)], "2H", 50)
        after = live_read_signature([self._goal(10), self._goal(55)], "2H", 55)
        assert before != after

    def test_new_red_changes_sig(self):
        before = live_read_signature([self._goal(10)], "2H", 50)
        after = live_read_signature([self._goal(10), self._red(52)], "2H", 52)
        assert before != after

    def test_status_transition_changes_sig(self):
        events = [self._goal(10)]
        assert live_read_signature(events, "1H", 45) != live_read_signature(events, "HT", 45)

    def test_yellow_card_does_not_change_sig(self):
        before = live_read_signature([self._goal(10)], "2H", 50)
        after = live_read_signature([self._goal(10), self._yellow(51)], "2H", 50)
        assert before == after

    def test_minute_within_bucket_unchanged(self):
        events = [self._goal(10)]
        m1 = REFRESH_MINUTES * 3 + 1
        m2 = REFRESH_MINUTES * 3 + (REFRESH_MINUTES - 1)
        assert live_read_signature(events, "2H", m1) == live_read_signature(events, "2H", m2)

    def test_minute_crossing_bucket_changes_sig(self):
        events = [self._goal(10)]
        before = live_read_signature(events, "2H", REFRESH_MINUTES * 3 - 1)
        after = live_read_signature(events, "2H", REFRESH_MINUTES * 3 + 1)
        assert before != after
