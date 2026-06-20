"""
CLI entrypoint: python -m app.data.collect --date YYYY-MM-DD

Fetches fixtures from API-Football for a given date, computes deterministic
group tables via standings_math, and upserts to DB. The API standings endpoint
is not used for persistence — computed tables are always the source of truth so
the standings page and the brief are always consistent.
Degrades gracefully on missing API key or network failure.
"""

import argparse
import logging
import sys
from collections import defaultdict
from datetime import date

from sqlalchemy import select

from app.config import settings
from app.data.api_football import APIFootballClient
from app.data.repository import (
    make_session_factory,
    matches_table,
    prune_matches_not_in,
    upsert_matches,
    upsert_standings_snapshot,
    upsert_teams,
    upsert_top_scorers,
)
from app.data.standings_math import compute_group_table, apply_position_deltas, qualification_status

log = logging.getLogger(__name__)


def _parse_date(val: str) -> date:
    return date.fromisoformat(val)


def run(target_date: date) -> int:
    if not settings.API_FOOTBALL_KEY:
        log.error("API_FOOTBALL_KEY not set — aborting data collection")
        return 1

    client = APIFootballClient()
    session_factory = make_session_factory()

    try:
        # Team metadata (incl. crest logos + group) comes from the standings
        # endpoint (structural); the table numbers below are still computed in
        # Python from results.
        log.info("Fetching teams + fixtures (league=%s season=%s)",
                 client._league_id, client._season)
        teams = client.get_teams()
        team_group = {t.name: t.group_name for t in teams if t.group_name}
        # Fetch the full tournament-to-date fixture set (not just one day) so the
        # computed standings snapshot is cumulative and correct, not single-day.
        matches = client.get_fixtures()
        log.info("Fetched %d fixtures, %d teams mapped to groups", len(matches), len(team_group))
    except Exception as exc:
        log.error("Failed to fetch data: %s", exc)
        return 1

    # Assign each GROUP-STAGE match its real group (A–L) via the team->group
    # map. Knockout matches (Round of 16, etc.) keep group_name=None so they are
    # persisted but never counted toward group standings.
    for m in matches:
        if m.stage and m.stage.lower().startswith("group"):
            m.group_name = team_group.get(m.home_team) or team_group.get(m.away_team)

    # Compute deterministic tables per group from actual results.
    by_group: dict[str, list] = defaultdict(list)
    for m in matches:
        if m.group_name:
            by_group[m.group_name].append(m)

    group_tables: dict[str, list] = {}
    for group_name, group_matches in by_group.items():
        group_tables[group_name] = compute_group_table(group_matches)

    # Compute qualification labels across all groups at once (best-thirds rule).
    qual_map = qualification_status(group_tables)
    for rows in group_tables.values():
        for row in rows:
            row.qualification = qual_map.get(row.team)

    snapshot_rows = [row for rows in group_tables.values() for row in rows]

    with session_factory() as session:
        try:
            upsert_matches(session, matches)
            # Drop any match not in the current fetch (e.g. a prior season's
            # rows) so the DB always reflects only the active tournament.
            removed = prune_matches_not_in(session, [m.fixture_id for m in matches])
            log.info("Upserted %d matches (pruned %d stale)", len(matches), removed)
        except Exception as exc:
            log.error("Failed to upsert matches: %s", exc)
            return 1

        try:
            if snapshot_rows:
                upsert_standings_snapshot(session, target_date, snapshot_rows)
                log.info("Upserted %d standing rows for %s", len(snapshot_rows), target_date)
        except Exception as exc:
            log.error("Failed to upsert standings: %s", exc)
            return 1

        try:
            upsert_teams(session, teams)
            log.info("Upserted %d teams (logos)", len(teams))
        except Exception as exc:
            log.error("Failed to upsert teams: %s", exc)
            return 1

        # Top scorers are a nice-to-have enrichment (1 extra API call). A failure
        # here (e.g. plan/season without topscorers access) must not abort the
        # whole collect — log and continue.
        try:
            scorers = client.get_top_scorers()
            upsert_top_scorers(session, client._season, scorers)
            log.info("Upserted %d top scorers (season %s)", len(scorers), client._season)
        except Exception as exc:
            log.warning("Top scorers enrichment skipped: %s", exc)

    log.info("Collection complete for %s", target_date)
    return 0


def collect_live(session_factory, client: APIFootballClient) -> int:
    """Lightweight refresh of in-play matches: fetch ?live=all and upsert only
    score/status/elapsed for fixtures we already track. No standings recompute,
    no LLM, no prune. Returns the number of live matches upserted.

    `?live=all` is league-agnostic, so results are intersected with stored
    fixture_ids to avoid persisting other competitions' live games.
    """
    live = client.get_fixtures(live=True)
    if not live:
        return 0
    with session_factory() as session:
        known = {fid for (fid,) in session.execute(select(matches_table.c.fixture_id)).all()}
        ours = [m for m in live if m.fixture_id in known]
        if ours:
            upsert_matches(session, ours)
    log.info("Live refresh: %d in-play (%d ours) upserted", len(live), len(ours))
    return len(ours)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect WC 2026 data for a date")
    parser.add_argument("--date", required=True, type=_parse_date, help="YYYY-MM-DD")
    args = parser.parse_args()

    from app.logging_config import configure_logging, stop_logging

    configure_logging()
    try:
        rc = run(args.date)
    finally:
        stop_logging()  # flush before this short-lived process exits
    sys.exit(rc)


if __name__ == "__main__":
    main()
