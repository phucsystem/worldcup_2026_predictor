"""
Unit tests for standings_math.py — pure functions, no I/O, no DB.
"""

import pytest
from app.data.models import Match, StandingRow
from app.data.standings_math import (
    compute_group_table,
    apply_position_deltas,
    rank_best_thirds,
    qualification_status,
)


def _match(fixture_id: int, home: str, away: str, hs: int | None, as_: int | None, group: str = "Group A") -> Match:
    return Match(
        fixture_id=fixture_id,
        group_name=group,
        home_team=home,
        away_team=away,
        home_score=hs,
        away_score=as_,
        status="FT" if hs is not None else "NS",
        kickoff_utc=None,
    )


# ---------------------------------------------------------------------------
# compute_group_table
# ---------------------------------------------------------------------------

class TestComputeGroupTable:
    def test_three_wins_nine_points(self):
        matches = [
            _match(1, "A", "B", 2, 0),
            _match(2, "A", "C", 1, 0),
            _match(3, "A", "D", 3, 1),
        ]
        table = compute_group_table(matches)
        a = next(r for r in table if r.team == "A")
        assert a.won == 3
        assert a.points == 9
        assert a.played == 3

    def test_draw_gives_one_point_each(self):
        matches = [_match(1, "X", "Y", 1, 1)]
        table = compute_group_table(matches)
        x = next(r for r in table if r.team == "X")
        y = next(r for r in table if r.team == "Y")
        assert x.points == 1
        assert y.points == 1
        assert x.drawn == 1
        assert y.drawn == 1

    def test_gf_ga_gd(self):
        matches = [_match(1, "A", "B", 3, 1)]
        table = compute_group_table(matches)
        a = next(r for r in table if r.team == "A")
        b = next(r for r in table if r.team == "B")
        assert a.gf == 3 and a.ga == 1 and a.gd == 2
        assert b.gf == 1 and b.ga == 3 and b.gd == -2

    def test_unplayed_matches_excluded(self):
        matches = [
            _match(1, "A", "B", 2, 1),
            _match(2, "C", "D", None, None),
        ]
        table = compute_group_table(matches)
        teams = {r.team for r in table}
        assert "A" in teams and "B" in teams
        # C and D have no completed matches → not in table
        assert "C" not in teams and "D" not in teams

    def test_sort_by_points_desc(self):
        # A wins all, B mid, C and D bottom
        matches = [
            _match(1, "A", "B", 2, 0),
            _match(2, "A", "C", 1, 0),
            _match(3, "A", "D", 1, 0),
            _match(4, "B", "C", 2, 0),
            _match(5, "B", "D", 1, 0),
            _match(6, "C", "D", 1, 1),
        ]
        table = compute_group_table(matches)
        assert table[0].team == "A"  # 9 pts
        assert table[1].team == "B"  # 6 pts

    def test_sort_tiebreak_gd_then_gf(self):
        """Two teams equal points: higher GD ranked first; if equal GD, higher GF."""
        matches = [
            # A: 3 pts, GD +2, GF=3
            _match(1, "A", "B", 3, 1),
            # C: 3 pts, GD +1, GF=2
            _match(2, "C", "D", 2, 1),
        ]
        table = compute_group_table(matches)
        # A has GD=2, C has GD=1 → A above C
        a_pos = next(r for r in table if r.team == "A").position
        c_pos = next(r for r in table if r.team == "C").position
        assert a_pos < c_pos

    def test_tiebreak_gf_when_gd_equal(self):
        """Equal points and GD: higher GF wins."""
        matches = [
            _match(1, "A", "X", 3, 1),   # A: 3pts, GD+2, GF=3
            _match(2, "B", "Y", 4, 2),   # B: 3pts, GD+2, GF=4
        ]
        table = compute_group_table(matches)
        b_pos = next(r for r in table if r.team == "B").position
        a_pos = next(r for r in table if r.team == "A").position
        assert b_pos < a_pos

    def test_position_assignment(self):
        matches = [
            _match(1, "A", "B", 3, 0),
            _match(2, "A", "C", 2, 0),
            _match(3, "A", "D", 1, 0),
            _match(4, "B", "C", 2, 1),
            _match(5, "B", "D", 1, 0),
            _match(6, "C", "D", 1, 0),
        ]
        table = compute_group_table(matches)
        positions = {r.team: r.position for r in table}
        assert positions["A"] == 1
        assert positions["B"] == 2
        assert positions["C"] == 3
        assert positions["D"] == 4

    def test_loss_gives_zero_points(self):
        matches = [_match(1, "A", "B", 0, 2)]
        table = compute_group_table(matches)
        a = next(r for r in table if r.team == "A")
        assert a.points == 0
        assert a.lost == 1


# ---------------------------------------------------------------------------
# apply_position_deltas
# ---------------------------------------------------------------------------

class TestApplyPositionDeltas:
    def test_prev_position_set_from_previous_snapshot(self):
        prev = [
            StandingRow(group_name="Group A", team="A", position=2),
            StandingRow(group_name="Group A", team="B", position=1),
        ]
        current = [
            StandingRow(group_name="Group A", team="A", position=1),
            StandingRow(group_name="Group A", team="B", position=2),
        ]
        result = apply_position_deltas(current, prev)
        a = next(r for r in result if r.team == "A")
        b = next(r for r in result if r.team == "B")
        assert a.prev_position == 2
        assert b.prev_position == 1

    def test_new_team_gets_none_prev_position(self):
        prev: list[StandingRow] = []
        current = [StandingRow(group_name="Group A", team="A", position=1)]
        result = apply_position_deltas(current, prev)
        assert result[0].prev_position is None


# ---------------------------------------------------------------------------
# rank_best_thirds
# ---------------------------------------------------------------------------

def _group_table_with_third(
    group_name: str,
    third_team: str,
    points: int,
    gd: int,
    gf: int,
) -> list[StandingRow]:
    """Helper: returns a 4-row group with the 3rd-place team having given stats."""
    return [
        StandingRow(group_name=group_name, team=f"{group_name}_1st", points=9, gd=6, gf=6, position=1),
        StandingRow(group_name=group_name, team=f"{group_name}_2nd", points=6, gd=2, gf=4, position=2),
        StandingRow(group_name=group_name, team=third_team, points=points, gd=gd, gf=gf, position=3),
        StandingRow(group_name=group_name, team=f"{group_name}_4th", points=0, gd=-8, gf=0, position=4),
    ]


class TestRankBestThirds:
    def _build_12_groups(self, overrides: dict[str, tuple] | None = None) -> dict[str, list[StandingRow]]:
        """Build 12 group tables. overrides: {group_name: (points, gd, gf)} for 3rd place."""
        default = (3, 0, 1)
        groups = {}
        for letter in "ABCDEFGHIJKL":
            gname = f"Group {letter}"
            pts, gd, gf = (overrides or {}).get(gname, default)
            team = f"Team_{letter}3"
            groups[gname] = _group_table_with_third(gname, team, pts, gd, gf)
        return groups

    def test_exactly_8_teams_returned(self):
        tables = self._build_12_groups()
        result = rank_best_thirds(tables)
        assert len(result) == 8

    def test_top_8_by_points(self):
        # Groups A-H thirds have 5 pts, I-L thirds have 1 pt
        overrides = {f"Group {c}": (5, 0, 1) for c in "ABCDEFGH"}
        overrides.update({f"Group {c}": (1, 0, 1) for c in "IJKL"})
        tables = self._build_12_groups(overrides)
        result = rank_best_thirds(tables)
        # All 8 selected should be from groups A-H
        for team in result:
            letter = team.split("_")[1][0]  # "Team_A3" → "A"
            assert letter in "ABCDEFGH"

    def test_tiebreak_at_8th_9th_boundary(self):
        """
        9 thirds with 4 pts. 8 of them have GD=1, one has GD=0.
        The GD=0 team must be excluded (ranked 9th).
        """
        overrides = {f"Group {c}": (4, 1, 2) for c in "ABCDEFGHI"}
        overrides["Group I"] = (4, 0, 2)  # GD=0: should be 9th
        overrides.update({f"Group {c}": (1, 0, 1) for c in "JKL"})
        tables = self._build_12_groups(overrides)
        result = rank_best_thirds(tables)
        assert len(result) == 8
        assert "Team_I3" not in result

    def test_tiebreak_gf_at_boundary(self):
        """
        Equal points + GD at the 8th/9th boundary: higher GF qualifies.
        """
        overrides = {f"Group {c}": (4, 1, 3) for c in "ABCDEFGH"}
        overrides["Group I"] = (4, 1, 1)  # same pts/GD, lower GF → 9th
        overrides.update({f"Group {c}": (1, 0, 1) for c in "JKL"})
        tables = self._build_12_groups(overrides)
        result = rank_best_thirds(tables)
        assert len(result) == 8
        assert "Team_I3" not in result

    def test_ranked_by_points_descending(self):
        """Top third should be the one with the most points."""
        overrides = {"Group A": (7, 3, 5)}
        tables = self._build_12_groups(overrides)
        result = rank_best_thirds(tables)
        assert result[0] == "Team_A3"

    def test_fewer_than_12_groups_returns_at_most_8(self):
        """With only 4 groups, return all 4 thirds (< 8)."""
        tables = {
            f"Group {c}": _group_table_with_third(f"Group {c}", f"Team_{c}3", 3, 0, 1)
            for c in "ABCD"
        }
        result = rank_best_thirds(tables)
        assert len(result) == 4


# ---------------------------------------------------------------------------
# qualification_status
# ---------------------------------------------------------------------------

def _full_group(group_name: str, teams_pts: list[tuple[str, int, int, int]]) -> list[StandingRow]:
    """teams_pts: [(team, points, gd, gf)] sorted best-first, all played=3."""
    rows = []
    for i, (team, pts, gd, gf) in enumerate(teams_pts, start=1):
        rows.append(StandingRow(
            group_name=group_name, team=team,
            played=3, points=pts, gd=gd, gf=gf, position=i,
            won=pts // 3, drawn=pts % 3, lost=3 - (pts // 3) - (pts % 3),
            ga=gf - gd,
        ))
    return rows


class TestQualificationStatus:
    def test_complete_group_top_2_qualified(self):
        rows = _full_group("Group A", [
            ("TeamA1", 9, 6, 7),
            ("TeamA2", 6, 2, 4),
            ("TeamA3", 3, -1, 2),
            ("TeamA4", 0, -7, 0),
        ])
        tables = {"Group A": rows}
        # Build 11 more groups with low-scoring thirds so TeamA3 doesn't make top-8
        for letter in "BCDEFGHIJK":
            gname = f"Group {letter}"
            tables[gname] = _full_group(gname, [
                (f"{letter}1", 9, 6, 7), (f"{letter}2", 6, 2, 4),
                (f"{letter}3", 4, 1, 3), (f"{letter}4", 0, -9, 0),
            ])
        tables["Group L"] = _full_group("Group L", [
            ("L1", 9, 6, 7), ("L2", 6, 2, 4),
            ("L3", 4, 1, 3), ("L4", 0, -9, 0),
        ])
        status = qualification_status(tables)
        assert status["TeamA1"] == "qualified"
        assert status["TeamA2"] == "qualified"
        assert status["TeamA4"] == "eliminated"

    def test_third_place_in_top_8_is_qualified(self):
        """A 3rd-place team with the best stats across all groups should be qualified."""
        tables = {}
        for letter in "ABCDEFGHIJKL":
            gname = f"Group {letter}"
            # Give Group A's 3rd place 7 pts (outstanding), all others 3 pts
            third_pts = 7 if letter == "A" else 3
            third_gd = 5 if letter == "A" else 0
            third_gf = 7 if letter == "A" else 1
            tables[gname] = _full_group(gname, [
                (f"{letter}1", 9, 6, 7), (f"{letter}2", 6, 2, 4),
                (f"{letter}3", third_pts, third_gd, third_gf), (f"{letter}4", 0, -8, 0),
            ])
        status = qualification_status(tables)
        assert status["A3"] == "qualified"

    def test_third_place_outside_top_8_is_eliminated(self):
        """A 3rd-place team that doesn't make top-8 thirds is eliminated."""
        tables = {}
        for letter in "ABCDEFGHIJKL":
            gname = f"Group {letter}"
            # Groups A-H have 3rd with 5 pts, I-L have 3 pts → Group L's 3rd is 9th
            third_pts = 5 if letter in "ABCDEFGH" else 3
            tables[gname] = _full_group(gname, [
                (f"{letter}1", 9, 6, 7), (f"{letter}2", 6, 2, 4),
                (f"{letter}3", third_pts, 0, 1), (f"{letter}4", 0, -8, 0),
            ])
        status = qualification_status(tables)
        # I, J, K, L thirds have 3 pts — outside top-8 (8 teams all have 5 pts)
        assert status["I3"] == "eliminated"
        assert status["L3"] == "eliminated"
