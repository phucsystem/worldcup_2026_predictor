"""
Unit tests for the pure shaping functions in app.api.fixtures — no DB, no network.
"""

from datetime import datetime, timezone

from app.api.fixtures import (
    _safe_live_winprob,
    _safe_live_winprob_history,
    is_knockout_stage,
    is_live_status,
    shape_knockout,
    shape_live,
    shape_upcoming,
)


def _dt(y, m, d, h=12):
    return datetime(y, m, d, h, 0, tzinfo=timezone.utc)


def _match(
    fid, home, away, kickoff, stage=None, group=None, hs=None, as_=None,
    status="NS", elapsed=None, updated_at=None,
):
    return {
        "fixture_id": fid,
        "home_team": home,
        "away_team": away,
        "home_score": hs,
        "away_score": as_,
        "status": status,
        "elapsed": elapsed,
        "stage": stage,
        "group_name": group,
        "kickoff_utc": kickoff,
        "updated_at": updated_at,
    }


LOGOS = {"France": "https://img/fr.png", "Brazil": "https://img/br.png"}


# ---------------------------------------------------------------------------
# is_knockout_stage
# ---------------------------------------------------------------------------

class TestIsKnockoutStage:
    def test_recognises_known_rounds_case_insensitive(self):
        assert is_knockout_stage("Round of 16")
        assert is_knockout_stage("round of 16")
        assert is_knockout_stage("Final")
        assert is_knockout_stage("Quarter-finals")

    def test_rejects_group_and_empty(self):
        assert not is_knockout_stage("Group Stage - 1")
        assert not is_knockout_stage(None)
        assert not is_knockout_stage("")


# ---------------------------------------------------------------------------
# shape_upcoming
# ---------------------------------------------------------------------------

class TestShapeUpcoming:
    def test_groups_by_day_ascending_and_picks_up_next(self):
        # Times chosen to stay within the same Australia/Melbourne (UTC+10) day
        # after conversion: 06:00Z = 16:00 local, still June 13.
        rows = [
            _match(2, "France", "Brazil", _dt(2026, 6, 13, 6)),
            _match(1, "France", "Brazil", _dt(2026, 6, 12, 9)),
            _match(3, "Brazil", "France", _dt(2026, 6, 13, 2)),
        ]
        out = shape_upcoming(rows, LOGOS)
        assert [d.date.isoformat() for d in out.days] == ["2026-06-12", "2026-06-13"]
        # within a day, sorted by kickoff time
        assert [f.fixture_id for f in out.days[1].fixtures] == [3, 2]
        # up_next is the soonest overall
        assert out.up_next.fixture_id == 1

    def test_buckets_by_brief_timezone_not_utc(self):
        # 17:00Z is 03:00 the NEXT day in Australia/Melbourne (UTC+10), so the
        # match must land on June 21 — not June 20 as naive UTC bucketing did.
        rows = [_match(1, "France", "Brazil", _dt(2026, 6, 20, 17))]
        out = shape_upcoming(rows, LOGOS)
        assert [d.date.isoformat() for d in out.days] == ["2026-06-21"]

    def test_enriches_logos(self):
        rows = [_match(1, "France", "Brazil", _dt(2026, 6, 12))]
        out = shape_upcoming(rows, LOGOS)
        f = out.days[0].fixtures[0]
        assert f.home_logo == "https://img/fr.png"
        assert f.away_logo == "https://img/br.png"

    def test_missing_logo_is_none(self):
        rows = [_match(1, "Qatar", "Ecuador", _dt(2026, 6, 12))]
        out = shape_upcoming(rows, LOGOS)
        assert out.days[0].fixtures[0].home_logo is None

    def test_empty(self):
        out = shape_upcoming([], LOGOS)
        assert out.up_next is None
        assert out.days == []


# ---------------------------------------------------------------------------
# is_live_status / shape_live
# ---------------------------------------------------------------------------

class TestIsLiveStatus:
    def test_in_play_codes_are_live(self):
        for s in ("1H", "HT", "2H", "ET", "BT", "P", "LIVE"):
            assert is_live_status(s)

    def test_not_started_and_finished_are_not_live(self):
        for s in ("NS", "FT", "AET", "PEN", "PST", "CANC", None, ""):
            assert not is_live_status(s)


class TestShapeLive:
    def test_filters_to_live_only(self):
        rows = [
            _match(1, "France", "Brazil", _dt(2026, 6, 19, 10), status="NS"),
            _match(2, "France", "Brazil", _dt(2026, 6, 19, 8), status="2H", hs=1, as_=0, elapsed=67),
            _match(3, "Brazil", "France", _dt(2026, 6, 18, 12), status="FT", hs=2, as_=1),
            _match(4, "France", "Brazil", _dt(2026, 6, 19, 9), status="HT", hs=0, as_=0, elapsed=45),
        ]
        out = shape_live(rows, LOGOS)
        assert [f.fixture_id for f in out] == [2, 4]  # live only, soonest-kicked first

    def test_preserves_elapsed_and_score(self):
        rows = [_match(2, "France", "Brazil", _dt(2026, 6, 19, 8), status="2H", hs=1, as_=0, elapsed=67)]
        out = shape_live(rows, LOGOS)
        assert out[0].elapsed == 67
        assert out[0].home_score == 1
        assert out[0].away_score == 0
        assert out[0].home_logo == "https://img/fr.png"

    def test_empty_when_none_live(self):
        rows = [_match(1, "France", "Brazil", _dt(2026, 6, 19), status="NS")]
        assert shape_live(rows, LOGOS) == []


# ---------------------------------------------------------------------------
# shape_knockout
# ---------------------------------------------------------------------------

class TestShapeKnockout:
    def test_orders_rounds_canonically(self):
        rows = [
            _match(1, "A", "B", _dt(2026, 7, 10), stage="Final"),
            _match(2, "C", "D", _dt(2026, 7, 1), stage="Round of 16"),
            _match(3, "E", "F", _dt(2026, 7, 5), stage="Semi-finals"),
        ]
        out = shape_knockout(rows, LOGOS)
        assert [r.round for r in out.rounds] == ["Round of 16", "Semi-finals", "Final"]

    def test_groups_multiple_ties_per_round_sorted_by_kickoff(self):
        rows = [
            _match(1, "A", "B", _dt(2026, 7, 1, 18), stage="Round of 16"),
            _match(2, "C", "D", _dt(2026, 7, 1, 12), stage="Round of 16"),
        ]
        out = shape_knockout(rows, LOGOS)
        assert len(out.rounds) == 1
        assert [t.fixture_id for t in out.rounds[0].ties] == [2, 1]

    def test_ignores_non_knockout_rows(self):
        rows = [
            _match(1, "A", "B", _dt(2026, 6, 12), stage="Group Stage - 1", group="Group A"),
            _match(2, "C", "D", _dt(2026, 7, 1), stage="Round of 16"),
        ]
        out = shape_knockout(rows, LOGOS)
        assert len(out.rounds) == 1
        assert out.rounds[0].round == "Round of 16"

    def test_carries_scores_for_completed_ties(self):
        rows = [_match(1, "France", "Brazil", _dt(2026, 7, 1), stage="Final", hs=2, as_=1, status="FT")]
        out = shape_knockout(rows, LOGOS)
        tie = out.rounds[0].ties[0]
        assert tie.home_score == 2 and tie.away_score == 1

    def test_empty_bracket(self):
        out = shape_knockout([], LOGOS)
        assert out.rounds == []


class TestSafeLiveWinProb:
    def test_valid_blob_maps(self):
        wp = _safe_live_winprob({"home": 55, "draw": 25, "away": 20})
        assert wp is not None
        assert (wp.home, wp.draw, wp.away) == (55, 25, 20)

    def test_none_and_empty_degrade_to_none(self):
        assert _safe_live_winprob(None) is None
        assert _safe_live_winprob({}) is None

    def test_malformed_blob_degrades_to_none(self):
        assert _safe_live_winprob({"home": 55}) is None          # missing keys
        assert _safe_live_winprob("not-a-dict") is None


class TestSafeLiveWinProbHistory:
    def _point(self, **kw):
        base = {"minute": 30, "home_pct": 50, "draw_pct": 30, "away_pct": 20,
                "home_score": 1, "away_score": 0, "label": "Goal · Brazil"}
        base.update(kw)
        return base

    def test_valid_points_map(self):
        pts = _safe_live_winprob_history([self._point(minute=0, label="KO"), self._point()])
        assert len(pts) == 2
        assert pts[0].label == "KO"
        assert pts[1].minute == 30

    def test_non_list_degrades_to_empty(self):
        assert _safe_live_winprob_history(None) == []
        assert _safe_live_winprob_history({"minute": 1}) == []

    def test_malformed_point_dropped_rest_kept(self):
        pts = _safe_live_winprob_history([{"minute": 5}, self._point()])
        assert len(pts) == 1  # the malformed point is dropped, the good one kept
        assert pts[0].minute == 30
