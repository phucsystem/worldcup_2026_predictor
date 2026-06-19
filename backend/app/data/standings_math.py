"""
Pure standings computation for WC 2026 group stage.

Tiebreak simplification (V1): points → GD → GF.
FIFA rules also use head-to-head results before GD, but that's omitted for V1
as it requires cross-referencing individual fixtures. This note documents the
intentional deviation.
"""

from collections import defaultdict
from typing import Sequence

from app.data.models import Match, StandingRow

_POINTS_WIN = 3
_POINTS_DRAW = 1
_MATCHES_PER_TEAM = 3  # WC group stage: each team plays 3 matches


def compute_group_table(matches_for_group: Sequence[Match]) -> list[StandingRow]:
    """Build a standings table from completed matches within a single group."""
    stats: dict[str, dict] = defaultdict(lambda: {
        "played": 0, "won": 0, "drawn": 0, "lost": 0,
        "gf": 0, "ga": 0, "points": 0,
    })
    # Derive group_name once from input so it is stable regardless of iteration order.
    group_name = matches_for_group[0].group_name if matches_for_group else ""
    group_name = group_name or ""

    for m in matches_for_group:
        if m.home_score is None or m.away_score is None:
            continue
        if not m.home_team or not m.away_team:
            continue

        hs, as_ = m.home_score, m.away_score

        for team, gf, ga in [(m.home_team, hs, as_), (m.away_team, as_, hs)]:
            s = stats[team]
            s["played"] += 1
            s["gf"] += gf
            s["ga"] += ga
            if gf > ga:
                s["won"] += 1
                s["points"] += _POINTS_WIN
            elif gf == ga:
                s["drawn"] += 1
                s["points"] += _POINTS_DRAW
            else:
                s["lost"] += 1

    rows = []
    for team, s in stats.items():
        gd = s["gf"] - s["ga"]
        rows.append(StandingRow(
            group_name=group_name,
            team=team,
            played=s["played"],
            won=s["won"],
            drawn=s["drawn"],
            lost=s["lost"],
            gf=s["gf"],
            ga=s["ga"],
            gd=gd,
            points=s["points"],
        ))

    rows.sort(key=lambda r: (-r.points, -r.gd, -r.gf))
    for i, row in enumerate(rows, start=1):
        row.position = i

    return rows


def apply_position_deltas(
    current_rows: list[StandingRow],
    prev_rows: list[StandingRow],
) -> list[StandingRow]:
    """Annotate current rows with prev_position from the previous snapshot."""
    prev_lookup: dict[tuple[str, str], int | None] = {
        (r.group_name, r.team): r.position for r in prev_rows
    }
    for row in current_rows:
        row.prev_position = prev_lookup.get((row.group_name, row.team))
    return current_rows


def rank_best_thirds(all_group_tables: dict[str, list[StandingRow]]) -> list[str]:
    """
    WC 2026: 12 groups of 4. Top 2 from each group qualify (24 teams).
    8 best third-placed teams also qualify (total 32 teams).

    Returns team names of the 8 best thirds, ranked by points → GD → GF.
    """
    thirds: list[StandingRow] = []
    for rows in all_group_tables.values():
        position_3 = [r for r in rows if r.position == 3]
        if position_3:
            thirds.append(position_3[0])

    thirds.sort(key=lambda r: (-r.points, -r.gd, -r.gf))
    return [r.team for r in thirds[:8]]


def qualification_status(all_group_tables: dict[str, list[StandingRow]]) -> dict[str, str]:
    """
    Classify each team as 'qualified', 'eliminated', or 'contention'.

    For a complete group (all teams played 3 matches):
      - positions 1-2: qualified
      - position 3: qualified only if in top-8 thirds
      - position 4: eliminated

    For an incomplete group:
      - Mathematical clinch/elimination is simplified:
        a team with position 1-2 and enough points that 4th place cannot
        overtake them is 'qualified'; a team that cannot reach 3rd is
        'eliminated'; otherwise 'contention'.
    """
    qualified_thirds = set(rank_best_thirds(all_group_tables))
    result: dict[str, str] = {}

    for group_name, rows in all_group_tables.items():
        group_complete = all(r.played >= _MATCHES_PER_TEAM for r in rows)

        if group_complete:
            for row in rows:
                if row.position in (1, 2):
                    result[row.team] = "qualified"
                elif row.position == 3 and row.team in qualified_thirds:
                    result[row.team] = "qualified"
                else:
                    result[row.team] = "eliminated"
        else:
            # Simple in-progress heuristic: max points remaining = current + 3*(3-played)
            for row in rows:
                max_possible = row.points + _POINTS_WIN * (_MATCHES_PER_TEAM - row.played)
                # Sort others by current points to find the 2nd-best current points
                others = sorted(
                    [r for r in rows if r.team != row.team],
                    key=lambda r: -r.points,
                )
                if row.position in (1, 2):
                    # Clinched if no team outside top-2 can surpass this team's min possible
                    third_max = others[1].points + _POINTS_WIN * (_MATCHES_PER_TEAM - others[1].played) if len(others) >= 2 else 0
                    if row.points > third_max:
                        result[row.team] = "qualified"
                    else:
                        result[row.team] = "contention"
                else:
                    # Eliminated if team cannot reach 3rd place
                    second_min = others[0].points if others else 0
                    if max_possible < second_min:
                        result[row.team] = "eliminated"
                    else:
                        result[row.team] = "contention"

    return result
