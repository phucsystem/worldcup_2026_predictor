"""Insert ONE deterministic finished match (with events, statistics, and a
verdict) for end-to-end tests. Unlike seed_finished_match (which flips an
existing row), this inserts a self-contained fixture so e2e works on top of the
bare standings skeleton (seed_openfootball), with no API/LLM access.

  python -m app.data.seed_e2e_fixture            # insert/refresh the e2e fixture
  python -m app.data.seed_e2e_fixture --print-id # print the fixture id and exit

The two teams are picked from the seeded standings skeleton so the result also
surfaces in the home "Latest Results" widget (which links to /match/{id})."""
import argparse
import logging
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app.data.models import Match
from app.data.repository import (
    make_session_factory,
    matches_table,
    standings_table,
    upsert_matches,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Fixed, high id so it never collides with real API-Football fixture ids.
E2E_FIXTURE_ID = 990001


def _pick_two_teams(session) -> tuple[str, str, str]:
    """Two teams sharing a group from the latest standings snapshot."""
    snap = session.execute(
        select(standings_table.c.snapshot_date)
        .order_by(standings_table.c.snapshot_date.desc())
    ).first()
    if snap is None:
        return "Brazil", "Serbia", "Group G"  # fallback if skeleton absent
    rows = session.execute(
        select(standings_table.c.group_name, standings_table.c.team)
        .where(standings_table.c.snapshot_date == snap[0])
        .order_by(standings_table.c.group_name, standings_table.c.position)
    ).fetchall()
    by_group: dict[str, list[str]] = {}
    for group_name, team in rows:
        if team:
            by_group.setdefault(group_name, []).append(team)
    for group_name, teams in by_group.items():
        if len(teams) >= 2:
            return teams[0], teams[1], group_name
    return "Brazil", "Serbia", "Group G"


def _events(home: str, away: str) -> list[dict]:
    def ev(minute, team, player, type_="Goal", detail="Normal Goal"):
        return {
            "time": {"elapsed": minute, "extra": None},
            "team": {"name": team},
            "player": {"name": player},
            "assist": {"name": None},
            "type": type_,
            "detail": detail,
        }

    return [
        ev(23, away, f"{away} forward"),
        ev(40, home, f"{home} midfielder", type_="Card", detail="Yellow Card"),
        ev(51, home, f"{home} forward"),
        ev(64, home, f"{home} winger"),
        ev(78, home, f"{home} forward"),
    ]


def _statistics(home: str, away: str) -> list[dict]:
    def entry(name, poss, shots, sot, xg, corners):
        return {
            "team": {"name": name},
            "statistics": [
                {"type": "Ball Possession", "value": poss},
                {"type": "Total Shots", "value": shots},
                {"type": "Shots on Goal", "value": sot},
                {"type": "expected_goals", "value": xg},
                {"type": "Corner Kicks", "value": corners},
            ],
        }

    return [entry(home, "58%", 18, 8, "2.90", 8), entry(away, "42%", 10, 3, "1.20", 4)]


def seed() -> int:
    session_factory = make_session_factory()
    with session_factory() as session:
        home, away, group = _pick_two_teams(session)
        match = Match(
            fixture_id=E2E_FIXTURE_ID,
            group_name=group.replace("Group ", "") if group.startswith("Group ") else group,
            home_team=home,
            away_team=away,
            home_score=3,
            away_score=1,
            status="FT",
            elapsed=None,
            kickoff_utc=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            stage="Group Stage - 3",
            events=_events(home, away),
            statistics=_statistics(home, away),
            verdict_text=(
                f"{home} beat {away} 3-1, recovering from an early deficit to "
                f"score three unanswered second-half goals."
            ),
            verdict_model="seeded",
            forecast_json={
                "home_pct": 58,
                "draw_pct": 24,
                "away_pct": 18,
                "factors": [
                    {"name": "League position", "lean": "home", "why": f"{home} sits above {away} in the group table."},
                    {"name": "Points", "lean": "home", "why": f"{home} carries more points into the match."},
                    {"name": "Goal difference", "lean": "even", "why": "A narrow goal-difference gap separates the two."},
                ],
            },
            forecast_model="seeded",
        )
        upsert_matches(session, [match])
    log.info("Seeded e2e fixture %s (%s 3-1 %s)", E2E_FIXTURE_ID, home, away)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the deterministic e2e finished match")
    parser.add_argument("--print-id", action="store_true", help="print the fixture id and exit")
    args = parser.parse_args()
    if args.print_id:
        print(E2E_FIXTURE_ID)
        return
    sys.exit(seed())


if __name__ == "__main__":
    main()
