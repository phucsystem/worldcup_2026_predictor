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

    # One-time events backfill for finished matches still missing events. Bounded
    # (only un-backfilled finished fixtures) and fully guarded so it never aborts.
    try:
        backfill_finished_events(session_factory, client, matches)
    except Exception as exc:
        log.warning("Events backfill skipped: %s", exc)

    # One-time statistics backfill (possession/shots/xG/corners), same once-only
    # guard. Independent of events so one failing never blocks the other.
    try:
        backfill_finished_statistics(session_factory, client, matches)
    except Exception as exc:
        log.warning("Statistics backfill skipped: %s", exc)

    # One-time per-match verdict generation (DeepSeek narrates the score/scorers/
    # standings facts). Runs after events are backfilled so scorers are available.
    try:
        backfill_finished_verdicts(session_factory, matches, group_tables)
    except Exception as exc:
        log.warning("Verdict backfill skipped: %s", exc)

    log.info("Collection complete for %s", target_date)
    return 0


def collect_live(session_factory, client: APIFootballClient) -> int:
    """Lightweight refresh of in-play matches: fetch ?live=all and upsert only
    score/status/elapsed (+ events) for fixtures we already track. No standings
    recompute, no LLM, no prune. Returns the number of live matches upserted.

    `?live=all` is league-agnostic, so results are intersected with stored
    fixture_ids to avoid persisting other competitions' live games.
    """
    live = client.get_fixtures(live=True)
    if not live:
        return 0
    with session_factory() as session:
        known = {fid for (fid,) in session.execute(select(matches_table.c.fixture_id)).all()}
        ours = [m for m in live if m.fixture_id in known]
        # Attach the live event feed (incl. final events at FT) so the match page
        # timeline updates on the poll. A failed events fetch must not abort the
        # score/status upsert, so it is per-fixture guarded.
        for m in ours:
            try:
                m.events = client.get_events(m.fixture_id) or None
            except Exception as exc:
                log.warning("Live events fetch failed for %s: %s", m.fixture_id, exc)
            # Live statistics: re-fetched every poll (overwrite, no once-only guard
            # — that guard is for the finished-match backfill). Independently
            # guarded so a stats failure never drops the events/score upsert.
            try:
                m.statistics = client.get_fixture_statistics(m.fixture_id) or None
            except Exception as exc:
                log.warning("Live statistics fetch failed for %s: %s", m.fixture_id, exc)
        if ours:
            upsert_matches(session, ours)
    log.info("Live refresh: %d in-play (%d ours) upserted", len(live), len(ours))
    return len(ours)


def backfill_finished_events(session_factory, client: APIFootballClient, matches: list) -> int:
    """Fetch + store events once for finished matches that have none yet. Guarded
    so finished matches are never re-fetched on later runs. Returns the count
    backfilled. Any failure is logged and skipped — never aborts the collect."""
    from app.api.fixtures import select_fixtures_needing_events

    with session_factory() as session:
        existing = {
            fid
            for (fid, events) in session.execute(
                select(matches_table.c.fixture_id, matches_table.c.events_json)
            ).all()
            if events
        }
    needing = set(select_fixtures_needing_events(matches, existing))
    if not needing:
        return 0
    to_store = []
    for m in matches:
        if m.fixture_id not in needing:
            continue
        try:
            events = client.get_events(m.fixture_id)
        except Exception as exc:
            log.warning("Backfill events fetch failed for %s: %s", m.fixture_id, exc)
            continue
        if events:
            m.events = events
            to_store.append(m)
    if to_store:
        with session_factory() as session:
            upsert_matches(session, to_store)
    log.info("Backfilled events for %d finished matches", len(to_store))
    return len(to_store)


def backfill_finished_statistics(session_factory, client: APIFootballClient, matches: list) -> int:
    """Fetch + store match statistics once for finished matches that have none yet.
    Guarded so finished matches are never re-fetched on later runs. Returns the
    count backfilled. Any failure is logged and skipped — never aborts the collect."""
    from app.api.fixtures import select_fixtures_needing_statistics

    with session_factory() as session:
        existing = {
            fid
            for (fid, stats) in session.execute(
                select(matches_table.c.fixture_id, matches_table.c.statistics_json)
            ).all()
            if stats
        }
    needing = set(select_fixtures_needing_statistics(matches, existing))
    if not needing:
        return 0
    to_store = []
    for m in matches:
        if m.fixture_id not in needing:
            continue
        try:
            stats = client.get_fixture_statistics(m.fixture_id)
        except Exception as exc:
            log.warning("Backfill statistics fetch failed for %s: %s", m.fixture_id, exc)
            continue
        if stats:
            m.statistics = stats
            to_store.append(m)
    if to_store:
        with session_factory() as session:
            upsert_matches(session, to_store)
    log.info("Backfilled statistics for %d finished matches", len(to_store))
    return len(to_store)


def backfill_finished_verdicts(session_factory, matches: list, group_tables: dict) -> int:
    """Generate + store a one-line verdict once for finished matches that have none
    yet. Keep-last-good: a failed/empty generation never overwrites a stored
    verdict. Any failure is logged and skipped — never aborts the collect. Skipped
    entirely when no DEEPSEEK_API_KEY is configured. Returns the count stored."""
    if not settings.DEEPSEEK_API_KEY:
        return 0
    from app.api.fixtures import normalize_events, select_fixtures_needing_verdict
    from app.pipeline.verdict import build_match_verdict_facts, generate_match_verdict

    with session_factory() as session:
        rows = session.execute(
            select(
                matches_table.c.fixture_id,
                matches_table.c.verdict_text,
                matches_table.c.events_json,
            )
        ).all()
    existing = {fid for (fid, verdict, _ev) in rows if verdict}
    events_by_id = {fid: ev for (fid, _v, ev) in rows}
    needing = set(select_fixtures_needing_verdict(matches, existing))
    if not needing:
        return 0
    to_store = []
    for m in matches:
        if m.fixture_id not in needing:
            continue
        events = normalize_events(events_by_id.get(m.fixture_id), m.home_team, m.away_team)
        facts = build_match_verdict_facts(
            home_team=m.home_team,
            away_team=m.away_team,
            home_score=m.home_score,
            away_score=m.away_score,
            events=events,
            group_name=m.group_name,
            group_rows=group_tables.get(m.group_name or "", []),
        )
        try:
            result = generate_match_verdict(facts)
        except Exception as exc:
            log.warning("Verdict generation failed for %s: %s", m.fixture_id, exc)
            continue
        if result:
            m.verdict_text, m.verdict_model = result
            to_store.append(m)
    if to_store:
        with session_factory() as session:
            upsert_matches(session, to_store)
    log.info("Backfilled verdicts for %d finished matches", len(to_store))
    return len(to_store)


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
