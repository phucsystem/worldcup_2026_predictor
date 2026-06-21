"""Seed one stored match into a finished (S-10) state WITH match statistics and a
per-match verdict, for demoing the completed match page locally without a paid API
plan or an LLM call.

  python -m app.data.seed_finished_match                 # auto-pick a fixture
  python -m app.data.seed_finished_match --fixture-id N  # target a specific one
  python -m app.data.seed_finished_match --clear         # strip seeded stats/verdict/events

Sets status=FT, a 3-1 home win, raw events (goals + a card), a full statistics
payload (possession/shots/SoT/xG/corners) and a verdict. Scorer/verdict text is
illustrative placeholder built from the row's own team names — not real data.
"""
import argparse
import logging
import sys
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.data.repository import make_session_factory, matches_table

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _pick_fixture(session):
    return session.execute(
        select(matches_table.c.fixture_id, matches_table.c.home_team, matches_table.c.away_team)
        .where(matches_table.c.kickoff_utc.isnot(None))
        .order_by(matches_table.c.kickoff_utc.desc())
    ).first()


def _events_payload(home: str, away: str) -> list[dict]:
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


def _statistics_payload(home: str, away: str) -> list[dict]:
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

    return [
        entry(home, "58%", 18, 8, "2.90", 8),
        entry(away, "42%", 10, 3, "1.20", 4),
    ]


def seed(fixture_id: int | None, clear: bool) -> int:
    session_factory = make_session_factory()
    now = datetime.now(tz=timezone.utc)
    with session_factory() as session:
        if fixture_id is not None:
            row = session.execute(
                select(matches_table.c.fixture_id, matches_table.c.home_team, matches_table.c.away_team)
                .where(matches_table.c.fixture_id == fixture_id)
            ).first()
        else:
            row = _pick_fixture(session)
        if row is None:
            log.error("No fixtures in DB to seed")
            return 1
        fid, home, away = row[0], row[1] or "Home", row[2] or "Away"

        if clear:
            values = {
                "status": "FT",
                "events_json": None,
                "statistics_json": None,
                "verdict_text": None,
                "verdict_model": None,
                "updated_at": now,
            }
        else:
            values = {
                "status": "FT",
                "home_score": 3,
                "away_score": 1,
                "elapsed": None,
                "events_json": _events_payload(home, away),
                "statistics_json": _statistics_payload(home, away),
                "verdict_text": (
                    f"{home} beat {away} 3–1, recovering from an early deficit to "
                    f"score three unanswered second-half goals."
                ),
                "verdict_model": "seeded",
                "updated_at": now,
            }
        result = session.execute(
            update(matches_table).where(matches_table.c.fixture_id == fid).values(**values)
        )
        session.commit()
        if result.rowcount:
            log.info("%s fixture %s (%s vs %s)", "Cleared" if clear else "Seeded finished", fid, home, away)
        else:
            log.warning("Fixture %s not found", fid)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed/clear a finished match (stats + verdict) for demo")
    parser.add_argument("--fixture-id", type=int, default=None)
    parser.add_argument("--clear", action="store_true", help="strip seeded stats/verdict/events")
    args = parser.parse_args()
    sys.exit(seed(args.fixture_id, args.clear))


if __name__ == "__main__":
    main()
