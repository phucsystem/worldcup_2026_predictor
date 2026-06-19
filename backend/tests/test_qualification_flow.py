"""
Pure (no DB) test for the qualification_status end-to-end rule:
  - A 3rd-placed team that IS in the best-8 thirds → 'qualified'
  - A 3rd-placed team that is NOT in the best-8 thirds → 'eliminated' (completed group)

Guards the B1 fix: qualification_status() must correctly classify 3rd-placers
across all 12 groups using the best-thirds rule.
"""

import pytest
from app.data.models import StandingRow
from app.data.standings_math import qualification_status


def _completed_group(group_name: str, thirds_pts: int, thirds_gd: int, thirds_gf: int) -> list[StandingRow]:
    """Return a 4-row completed group (all played=3) with a controlled 3rd-place team."""
    return [
        StandingRow(group_name=group_name, team=f"{group_name}_1st", played=3,
                    points=9, gd=6, gf=7, position=1),
        StandingRow(group_name=group_name, team=f"{group_name}_2nd", played=3,
                    points=6, gd=2, gf=4, position=2),
        StandingRow(group_name=group_name, team=f"{group_name}_3rd", played=3,
                    points=thirds_pts, gd=thirds_gd, gf=thirds_gf, position=3),
        StandingRow(group_name=group_name, team=f"{group_name}_4th", played=3,
                    points=0, gd=-8, gf=0, position=4),
    ]


def _build_12_groups(strong_groups: set[str], strong_pts: int = 5, weak_pts: int = 2) -> dict[str, list[StandingRow]]:
    """
    Build 12 completed groups.
    strong_groups: group names whose 3rd-placer gets strong_pts (expected to qualify).
    Remaining groups get weak_pts (expected to be eliminated).
    """
    tables: dict[str, list[StandingRow]] = {}
    for letter in "ABCDEFGHIJKL":
        gname = f"Group {letter}"
        if gname in strong_groups:
            tables[gname] = _completed_group(gname, strong_pts, thirds_gd=1, thirds_gf=3)
        else:
            tables[gname] = _completed_group(gname, weak_pts, thirds_gd=0, thirds_gf=1)
    return tables


class TestQualificationFlow:
    def test_best_third_is_qualified(self):
        """
        8 groups have strong 3rd-placers (5 pts). 4 groups have weak 3rd-placers (2 pts).
        All 8 strong thirds must be 'qualified'; all 4 weak thirds must be 'eliminated'.
        """
        strong = {f"Group {c}" for c in "ABCDEFGH"}
        tables = _build_12_groups(strong)
        status = qualification_status(tables)

        for letter in "ABCDEFGH":
            team = f"Group {letter}_3rd"
            assert status[team] == "qualified", f"{team} should be qualified (in top-8 thirds)"

        for letter in "IJKL":
            team = f"Group {letter}_3rd"
            assert status[team] == "eliminated", f"{team} should be eliminated (outside top-8 thirds)"

    def test_non_qualifying_third_eliminated_not_contention(self):
        """
        In a completed group, a 3rd-place team outside the best-8 thirds must be
        'eliminated', never 'contention' (contention is only valid for incomplete groups).
        """
        strong = {f"Group {c}" for c in "ABCDEFGH"}
        tables = _build_12_groups(strong)
        status = qualification_status(tables)

        for letter in "IJKL":
            assert status[f"Group {letter}_3rd"] != "contention"

    def test_boundary_team_at_ninth_place_eliminated(self):
        """
        9 thirds all have 5 pts. 8 have GD=2, one (Group I) has GD=1.
        The GD=1 third is 9th → eliminated. Groups J–L have 2 pts → also eliminated.
        """
        tables: dict[str, list[StandingRow]] = {}
        for letter in "ABCDEFGH":
            gname = f"Group {letter}"
            tables[gname] = _completed_group(gname, thirds_pts=5, thirds_gd=2, thirds_gf=4)
        # Group I: same pts as A-H but lower GD → ranked 9th, outside top-8
        tables["Group I"] = _completed_group("Group I", thirds_pts=5, thirds_gd=1, thirds_gf=4)
        for letter in "JKL":
            gname = f"Group {letter}"
            tables[gname] = _completed_group(gname, thirds_pts=2, thirds_gd=0, thirds_gf=1)

        status = qualification_status(tables)

        for letter in "ABCDEFGH":
            assert status[f"Group {letter}_3rd"] == "qualified"
        assert status["Group I_3rd"] == "eliminated"

    def test_top_2_always_qualified_in_completed_group(self):
        """Positions 1 and 2 are always 'qualified' in a completed group."""
        strong = {f"Group {c}" for c in "ABCDEFGH"}
        tables = _build_12_groups(strong)
        status = qualification_status(tables)

        for letter in "ABCDEFGHIJKL":
            assert status[f"Group {letter}_1st"] == "qualified"
            assert status[f"Group {letter}_2nd"] == "qualified"

    def test_fourth_place_always_eliminated(self):
        """Position 4 is always 'eliminated' in a completed group."""
        strong = {f"Group {c}" for c in "ABCDEFGH"}
        tables = _build_12_groups(strong)
        status = qualification_status(tables)

        for letter in "ABCDEFGHIJKL":
            assert status[f"Group {letter}_4th"] == "eliminated"
