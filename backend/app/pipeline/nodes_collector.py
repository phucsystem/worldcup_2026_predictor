"""Collector node — no LLM. Assembles computed_facts from Phase 2 math."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from langsmith import traceable

from app.data.models import Match, StandingRow
from app.data.standings_math import (
    apply_position_deltas,
    compute_group_table,
    group_scenarios,
    qualification_status,
    rank_best_thirds,
)

_STAKE_GROUPS_CAP = 4  # home-page "What's at stake" shows up to 4 contention groups
from app.pipeline.state import BriefState


def _load_from_db(brief_date: date) -> tuple[list[Match], list[StandingRow]]:
    from app.data.repository import make_session_factory
    import sqlalchemy as sa
    from app.data.repository import matches_table, standings_table

    factory = make_session_factory()
    with factory() as session:
        m_rows = session.execute(sa.select(matches_table)).mappings().all()
        matches = [
            Match(
                fixture_id=r["fixture_id"],
                group_name=r["group_name"],
                home_team=r["home_team"],
                away_team=r["away_team"],
                home_score=r["home_score"],
                away_score=r["away_score"],
                status=r["status"],
                winner_side=r["winner_side"],
                home_pen=r["home_pen"],
                away_pen=r["away_pen"],
                kickoff_utc=r["kickoff_utc"],
                events=r["events_json"],
            )
            for r in m_rows
        ]

        s_rows = session.execute(
            sa.select(standings_table).where(
                standings_table.c.snapshot_date == brief_date
            )
        ).mappings().all()
        standings = [
            StandingRow(
                group_name=r["group_name"],
                team=r["team"],
                played=r["played"] or 0,
                won=r["won"] or 0,
                drawn=r["drawn"] or 0,
                lost=r["lost"] or 0,
                gf=r["gf"] or 0,
                ga=r["ga"] or 0,
                gd=r["gd"] or 0,
                points=r["points"] or 0,
                position=r["position"],
                prev_position=r["prev_position"],
            )
            for r in s_rows
        ]
    return matches, standings


def _build_facts(
    brief_date: date,
    matches: list[Match],
    standings: list[StandingRow],
) -> dict[str, Any]:
    by_group: dict[str, list[Match]] = defaultdict(list)
    for m in matches:
        if m.group_name:
            by_group[m.group_name].append(m)

    group_tables: dict[str, list[StandingRow]] = {}
    for group_name, gmatches in sorted(by_group.items()):
        rows = compute_group_table(gmatches)
        group_tables[group_name] = rows

    # Apply position deltas using provided standings snapshot as prev reference
    prev_lookup: dict[str, dict[str, int | None]] = defaultdict(dict)
    for row in standings:
        prev_lookup[row.group_name][row.team] = row.prev_position

    for group_name, rows in group_tables.items():
        prev_rows = [
            StandingRow(group_name=group_name, team=t, position=p)
            for t, p in prev_lookup.get(group_name, {}).items()
            if p is not None
        ]
        apply_position_deltas(rows, prev_rows)

    qual_status = qualification_status(group_tables)
    best_thirds = rank_best_thirds(group_tables)

    completed = [m for m in matches if m.home_score is not None and m.away_score is not None]
    upcoming = [
        m for m in matches
        if m.home_score is None
        and m.kickoff_utc
        and m.kickoff_utc > datetime.now(tz=timezone.utc)
    ]

    # Limit upcoming to next 8 to keep prompt bounded
    upcoming_sorted = sorted(upcoming, key=lambda m: m.kickoff_utc or datetime.max.replace(tzinfo=timezone.utc))[:8]

    # Candidate contention groups for the "What's at stake" cards: drop groups
    # that are fully decided (complete AND no team still in contention), rank the
    # rest by soonest upcoming fixture, cap at 4. The LLM narrates these; the
    # per-team `rows` notes are deterministic.
    _far = datetime.max.replace(tzinfo=timezone.utc)
    scenarios = group_scenarios(group_tables)
    stake_candidates: list[dict] = []
    for gname, rows in scenarios.items():
        group_rows = group_tables[gname]
        complete = all(r.played >= 3 for r in group_rows)
        has_contention = any(sr["status"] == "contention" for sr in rows)
        if complete and not has_contention:
            continue
        soonest = min(
            (m.kickoff_utc for m in upcoming if m.group_name == gname and m.kickoff_utc),
            default=None,
        )
        stake_candidates.append({
            "group_name": gname,
            "rows": rows,
            "next_kickoff_utc": soonest.isoformat() if soonest else None,
            "_sort": soonest or _far,
        })
    stake_candidates.sort(key=lambda c: c["_sort"])
    stake_groups = [
        {k: v for k, v in c.items() if k != "_sort"}
        for c in stake_candidates[:_STAKE_GROUPS_CAP]
    ]

    group_tables_serial: dict[str, list[dict]] = {}
    for gname, rows in group_tables.items():
        group_tables_serial[gname] = [
            {
                "position": r.position,
                "team": r.team,
                "played": r.played,
                "won": r.won,
                "drawn": r.drawn,
                "lost": r.lost,
                "gf": r.gf,
                "ga": r.ga,
                "gd": r.gd,
                "points": r.points,
                "prev_position": r.prev_position,
            }
            for r in rows
        ]

    return {
        "brief_date": brief_date.isoformat(),
        "total_matches_completed": len(completed),
        "total_matches_upcoming": len(upcoming),
        "completed_results": [
            {
                "fixture_id": m.fixture_id,
                "group": m.group_name,
                "home": m.home_team,
                "away": m.away_team,
                "score": f"{m.home_score}-{m.away_score}",
                "status": m.status,
            }
            for m in sorted(completed, key=lambda m: m.kickoff_utc or datetime.min.replace(tzinfo=timezone.utc))
        ],
        "upcoming_fixtures": [
            {
                "fixture_id": m.fixture_id,
                "group": m.group_name,
                "home": m.home_team,
                "away": m.away_team,
                "kickoff_utc": m.kickoff_utc.isoformat() if m.kickoff_utc else None,
            }
            for m in upcoming_sorted
        ],
        "group_tables": group_tables_serial,
        "best_third_place_teams": best_thirds,
        "qualification_status": qual_status,
        "stake_groups": stake_groups,
    }


@traceable(run_type="chain", name="collector")
def collector_node(state: BriefState) -> BriefState:
    t0 = time.perf_counter()
    brief_date = date.fromisoformat(state["brief_date"])

    matches_raw = state.get("matches") or []
    standings_raw = state.get("standings") or []

    if matches_raw:
        matches = [Match(**m) if isinstance(m, dict) else m for m in matches_raw]
        standings = [StandingRow(**s) if isinstance(s, dict) else s for s in standings_raw]
    else:
        matches, standings = _load_from_db(brief_date)

    facts = _build_facts(brief_date, matches, standings)

    elapsed = time.perf_counter() - t0
    timings = dict(state.get("node_timings") or {})
    timings["collector"] = round(elapsed, 3)

    return {
        **state,
        "computed_facts": facts,
        "node_timings": timings,
        "error": None,
    }
