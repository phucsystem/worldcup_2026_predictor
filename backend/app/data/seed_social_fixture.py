"""Insert ONE deterministic UPCOMING match carrying curated social highlights,
for local/e2e testing of the "What fans are saying" panel.

  python -m app.data.seed_social_fixture            # insert/refresh the fixture
  python -m app.data.seed_social_fixture --print-id # print the fixture id and exit

The free API-Football plan only covers 2021-2023, so a dev/CI env has no genuine
upcoming 2026 fixtures to crawl. This seed gives the preview-branch panel (and its
test) a stable upcoming fixture with a social_json blob to render — no API/LLM
access required. Mirrors seed_e2e_fixture's self-contained style."""
import argparse
import logging
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app.data.models import Match
from app.data.repository import (
    make_session_factory,
    standings_table,
    upsert_matches,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Fixed, high id so it never collides with real API-Football fixture ids or the
# finished e2e fixture (990001).
SOCIAL_FIXTURE_ID = 990002


def _pick_two_teams(session) -> tuple[str, str, str]:
    """Two teams sharing a group from the latest standings snapshot."""
    snap = session.execute(
        select(standings_table.c.snapshot_date)
        .order_by(standings_table.c.snapshot_date.desc())
    ).first()
    if snap is None:
        return "Argentina", "Mexico", "Group D"  # fallback if skeleton absent
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
    return "Argentina", "Mexico", "Group D"


def _highlights(home: str, away: str) -> dict:
    return {
        "highlights": [
            {
                "source": "reddit",
                "url": "https://www.reddit.com/r/worldcup/comments/example1",
                "author": "u/sample_fan",
                "posted_at": "2026-06-24T08:30:00Z",
                "text": (
                    f"{home}'s press has looked sharp all group stage — if {away} "
                    f"sit deep they'll get picked apart in the second half."
                ),
                "why": "tactical read on the matchup",
            },
            {
                "source": "bluesky",
                "url": "https://bsky.app/profile/sample.bsky.social/post/example2",
                "author": "sample.bsky.social",
                "posted_at": "2026-06-24T09:05:00Z",
                "text": (
                    f"Don't sleep on {away}'s counter — one quick transition and "
                    f"this is a different game."
                ),
                "why": "contrarian angle with engagement",
            },
        ]
    }


def seed() -> int:
    session_factory = make_session_factory()
    with session_factory() as session:
        home, away, group = _pick_two_teams(session)
        match = Match(
            fixture_id=SOCIAL_FIXTURE_ID,
            # Stored verbatim — both standings and matches use the "Group X" form,
            # so the fixture associates with its group correctly.
            group_name=group,
            home_team=home,
            away_team=away,
            home_score=None,
            away_score=None,
            status="NS",
            elapsed=None,
            kickoff_utc=datetime(2026, 6, 25, 18, 0, tzinfo=timezone.utc),
            stage="Group Stage - 3",
            social_json=_highlights(home, away),
            social_model="seeded",
        )
        upsert_matches(session, [match])
    log.info("Seeded upcoming social fixture %s (%s vs %s)", SOCIAL_FIXTURE_ID, home, away)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed an upcoming match with social highlights")
    parser.add_argument("--print-id", action="store_true", help="print the fixture id and exit")
    args = parser.parse_args()
    if args.print_id:
        print(SOCIAL_FIXTURE_ID)
        return
    sys.exit(seed())


if __name__ == "__main__":
    main()
