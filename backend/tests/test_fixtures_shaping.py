"""
Unit tests for the pure shaping functions in app.api.fixtures — no DB, no network.
"""

from datetime import datetime, timezone

from app.api.fixtures import (
    is_knockout_stage,
    shape_knockout,
    shape_upcoming,
)


def _dt(y, m, d, h=12):
    return datetime(y, m, d, h, 0, tzinfo=timezone.utc)


def _match(fid, home, away, kickoff, stage=None, group=None, hs=None, as_=None, status="NS"):
    return {
        "fixture_id": fid,
        "home_team": home,
        "away_team": away,
        "home_score": hs,
        "away_score": as_,
        "status": status,
        "stage": stage,
        "group_name": group,
        "kickoff_utc": kickoff,
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
        rows = [
            _match(2, "France", "Brazil", _dt(2026, 6, 13, 18)),
            _match(1, "France", "Brazil", _dt(2026, 6, 12, 9)),
            _match(3, "Brazil", "France", _dt(2026, 6, 13, 12)),
        ]
        out = shape_upcoming(rows, LOGOS)
        assert [d.date.isoformat() for d in out.days] == ["2026-06-12", "2026-06-13"]
        # within a day, sorted by kickoff time
        assert [f.fixture_id for f in out.days[1].fixtures] == [3, 2]
        # up_next is the soonest overall
        assert out.up_next.fixture_id == 1

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
