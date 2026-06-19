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

from app.config import settings
from app.data.api_football import APIFootballClient
from app.data.repository import make_session_factory, upsert_matches, upsert_standings_snapshot
from app.data.standings_math import compute_group_table, apply_position_deltas, qualification_status

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
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
        log.info("Fetching fixtures for %s", target_date)
        matches = client.get_fixtures(date_from=target_date, date_to=target_date)
        log.info("Fetched %d fixtures", len(matches))
    except Exception as exc:
        log.error("Failed to fetch fixtures: %s", exc)
        return 1

    # Group matches by group_name and compute deterministic tables.
    # API standings are intentionally not used for persistence: the computed
    # tables are derived from actual match results via standings_math, ensuring
    # the standings page and the daily brief always agree.
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
            log.info("Upserted %d matches", len(matches))
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

    log.info("Collection complete for %s", target_date)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect WC 2026 data for a date")
    parser.add_argument("--date", required=True, type=_parse_date, help="YYYY-MM-DD")
    args = parser.parse_args()
    sys.exit(run(args.date))


if __name__ == "__main__":
    main()
