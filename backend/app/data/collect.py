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

# Mirror of repository._FINISHED_STATUSES; kept local to avoid importing the API
# layer into the collector. Used to skip injury attachment on finished fixtures.
_FINISHED_FIXTURE_STATUSES = {"FT", "AET", "PEN"}


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

    # Injuries: one league+season API call, attached per fixture so the team-status
    # panel can show who is out / doubtful. Fully guarded — a plan without injury
    # access must never abort the collect. We set the list for every NON-finished
    # fixture (empty when none) so a recovered player clears rather than lingering;
    # finished fixtures are left untouched (team status isn't rendered for them).
    try:
        injuries_by_fixture = client.get_injuries()
    except Exception as exc:
        injuries_by_fixture = None
        log.warning("Injuries fetch skipped: %s", exc)
    if injuries_by_fixture is not None:
        attached = 0
        for m in matches:
            if (m.status or "").strip().upper() in _FINISHED_FIXTURE_STATUSES:
                continue
            recs = injuries_by_fixture.get(m.fixture_id) or []
            m.injuries_json = {"players": recs}
            if recs:
                attached += 1
        log.info("Attached injuries to %d upcoming fixtures", attached)

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

    # One-time per-match pre-kickoff forecast (DeepSeek estimates a win/draw/win
    # split + driving factors from each group-stage match's standings facts).
    try:
        backfill_forecasts(session_factory, matches, group_tables)
    except Exception as exc:
        log.warning("Forecast backfill skipped: %s", exc)

    # Daily-refreshed fan-discussion highlights for upcoming group-stage matches
    # (free Reddit/Bluesky → DeepSeek curation). Runs last, fully guarded, and
    # no-ops without social creds or a DeepSeek key — never blocks the collect.
    try:
        backfill_social_highlights(session_factory, matches)
    except Exception as exc:
        log.warning("Social highlights backfill skipped: %s", exc)

    log.info("Collection complete for %s", target_date)
    return 0


def collect_live(session_factory, client: APIFootballClient) -> int:
    """Lightweight refresh of in-play matches: fetch ?live=all and upsert
    score/status/elapsed (+ events + live statistics) for fixtures we already
    track, plus the hybrid live win-probability. No standings recompute, no prune.
    Returns the number of live matches upserted.

    `?live=all` is league-agnostic, so results are intersected with stored
    fixture_ids to avoid persisting other competitions' live games.

    Win-prob (group-stage only): every poll computes the Python base and re-applies
    the last stored bounded adjustment — pure, no LLM. The agent that *sets* that
    adjustment + the live read runs only on a significant-event signature change
    (goal / red / status / ~15' bucket), and is gated on DEEPSEEK_API_KEY.
    """
    live = client.get_fixtures(live=True)
    if not live:
        return 0
    with session_factory() as session:
        stored = {
            r["fixture_id"]: r
            for r in session.execute(
                select(
                    matches_table.c.fixture_id,
                    matches_table.c.group_name,
                    matches_table.c.forecast_json,
                    matches_table.c.live_winprob_adj_json,
                    matches_table.c.live_winprob_history_json,
                    matches_table.c.live_read_sig,
                )
            ).mappings().all()
        }
        ours = [m for m in live if m.fixture_id in stored]
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
            # Hybrid win-prob + live read. Fully guarded so a failure here never
            # drops the score/events/stats upsert that precedes it.
            try:
                _update_live_winprob(session, m, stored.get(m.fixture_id))
            except Exception as exc:
                log.warning("Live win-prob update failed for %s: %s", m.fixture_id, exc)
        if ours:
            upsert_matches(session, ours)
    log.info("Live refresh: %d in-play (%d ours) upserted", len(live), len(ours))
    return len(ours)


# Max win-prob history points kept per match (events + a point every ~15' stays
# well under this for a single match).
_WINPROB_HISTORY_CAP = 30


def _update_live_winprob(session, m, stored) -> None:
    """Compute the hybrid live win-prob for one in-play match and stage it on `m`
    for the upsert. Group-stage only (knockout has no prior/qualification, matching
    the forecast boundary). The Python base + stored adjustment recompute every poll
    (no LLM); the agent (Phase 3) refreshes the adjustment + read only on a
    significant-event signature change."""
    from app.api.fixtures import is_live_status, normalize_events
    from app.pipeline.winprob import (
        apply_adjustment,
        compute_base,
        live_read_signature,
    )

    group_name = (stored or {}).get("group_name")
    if not group_name or not is_live_status(m.status):
        return  # knockout / not actually in play → no win-prob

    events = normalize_events(m.events, m.home_team, m.away_team)
    home_red = sum(
        1 for e in events
        if (e.type or "").lower() == "card" and "red" in (e.detail or "").lower() and e.side == "home"
    )
    away_red = sum(
        1 for e in events
        if (e.type or "").lower() == "card" and "red" in (e.detail or "").lower() and e.side == "away"
    )
    minute = m.elapsed or 0
    base = compute_base(
        m.home_score or 0, m.away_score or 0, minute,
        prior=(stored or {}).get("forecast_json"),
        home_red=home_red, away_red=away_red,
    )

    new_sig = live_read_signature(events, m.status, minute)
    stored_sig = (stored or {}).get("live_read_sig")
    stored_adj = (stored or {}).get("live_winprob_adj_json")
    sig_changed = new_sig != stored_sig

    # On a significant-event signature change, the agent refreshes the bounded
    # adjustment + the live read in ONE call (gated on DEEPSEEK_API_KEY). On any
    # other poll the stored adjustment is simply re-applied — pure, no LLM.
    effective_adj = stored_adj
    if sig_changed and settings.DEEPSEEK_API_KEY:
        agent_result = _run_live_agent(session, m, base, events, group_name, minute)
        if agent_result is not None:
            payload, model = agent_result
            m.live_winprob_adj_json = payload["adjustment"]
            m.live_read_text = payload["read"]
            m.live_read_model = model
            m.live_read_sig = new_sig
            effective_adj = m.live_winprob_adj_json

    m.live_winprob_json = apply_adjustment(base, effective_adj)

    # Append one history point per significant-event change (not per poll).
    if sig_changed:
        history = list((stored or {}).get("live_winprob_history_json") or [])
        if not history:
            # Seed a kickoff point from the pre-match forecast. If the poller first
            # observes a match already in play (e.g. process restart mid-match) the
            # series simply starts from this KO anchor — an accepted approximation
            # of the early swing, not a reconstruction of it.
            prior = (stored or {}).get("forecast_json") or {}
            history.append({
                "minute": 0,
                "home_score": 0,
                "away_score": 0,
                "home_pct": prior.get("home_pct", base["home"]),
                "draw_pct": prior.get("draw_pct", base["draw"]),
                "away_pct": prior.get("away_pct", base["away"]),
                "label": "KO",
            })
        prev_minute = history[-1]["minute"] if history else 0
        history.append({
            "minute": minute,
            "home_score": m.home_score or 0,
            "away_score": m.away_score or 0,
            "home_pct": m.live_winprob_json["home"],
            "draw_pct": m.live_winprob_json["draw"],
            "away_pct": m.live_winprob_json["away"],
            "label": _history_label(events, minute, prev_minute),
        })
        m.live_winprob_history_json = history[-_WINPROB_HISTORY_CAP:]


def _run_live_agent(session, m, base, events, group_name, minute):
    """Build the agent fact bundle (signals + standings) and run the one DeepSeek
    call. Returns (payload, model) or None (keep-last-good). Standings are read from
    the latest snapshot; absent rows simply mean the signals omit form/qualification."""
    from app.data.repository import latest_standings_for_group
    from app.pipeline.live_winprob_agent import build_agent_facts, generate_live_winprob
    from app.pipeline.winprob import extract_signals

    rows = latest_standings_for_group(session, group_name)
    home_row = next((r for r in rows if r.team == m.home_team), None)
    away_row = next((r for r in rows if r.team == m.away_team), None)
    signals = extract_signals(
        statistics=m.statistics, events=events,
        home_team=m.home_team, away_team=m.away_team,
        home_row=home_row, away_row=away_row,
    )
    qualification = {
        k: v for k, v in (
            ("home", getattr(home_row, "qualification", None)),
            ("away", getattr(away_row, "qualification", None)),
        ) if v
    }
    facts = build_agent_facts(
        home_team=m.home_team, away_team=m.away_team,
        home_score=m.home_score, away_score=m.away_score,
        minute=minute, status=m.status, base=base, signals=signals,
        events=events, qualification=qualification or None,
    )
    return generate_live_winprob(facts)


def _history_label(events, minute, prev_minute) -> str:
    """Label for a new history point. If a goal or red card occurred since the last
    recorded point, name it ("Goal · Brazil"); otherwise this is a periodic-bucket
    or status refresh, so label it with the minute ("64'")."""
    def latest_since(kind_check):
        candidates = [e for e in events if kind_check(e) and (e.minute or 0) > prev_minute]
        return max(candidates, key=lambda e: e.minute or 0) if candidates else None

    goal = latest_since(lambda e: (e.type or "").lower() == "goal")
    if goal:
        return f"Goal · {goal.team}" if goal.team else "Goal"
    red = latest_since(
        lambda e: (e.type or "").lower() == "card" and "red" in (e.detail or "").lower()
    )
    if red:
        return f"Red · {red.team}" if red.team else "Red card"
    return f"{minute}'"


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


def _find_team_row_across_groups(group_tables: dict, team: str):
    """Search all groups for a team's StandingRow. Returns the first match or None."""
    for rows in group_tables.values():
        for r in rows:
            if r.team == team:
                return r
    return None


def _build_forecast_signals(
    session,
    home_team: str,
    away_team: str,
    injuries_json,
    matches: list,
    home_row=None,
    away_row=None,
) -> dict:
    """Assemble the enrichment signals dict for one match. Returns a dict with
    "home" and "away" keys — each containing whichever signals are available.
    Never raises; missing sources produce absent keys rather than fabricated data."""
    from app.data.fifa_rankings import get_fifa_rank
    from app.data.marquee_players import get_marquee_players
    from app.data.repository import top_scorers_table
    from app.pipeline.forecast_signals import (
        build_form_signal,
        build_injury_signal,
        build_strength_signal,
    )

    # Top scorers keyed by team from DB
    try:
        scorer_rows = session.execute(select(top_scorers_table)).mappings().all()
    except Exception:
        scorer_rows = []

    from app.data.models import TopScorer
    scorers_by_team: dict[str, list] = {}
    for row in scorer_rows:
        team = row.get("team")
        if not team:
            continue
        ts = TopScorer(
            player_id=row["player_id"],
            name=row["name"],
            team=team,
            goals=row.get("goals") or 0,
        )
        scorers_by_team.setdefault(team, []).append(ts)

    # Recent finished matches (from the in-memory list — already fetched this run)
    _FINISHED = {"FT", "AET", "PEN"}

    def finished_for(team: str) -> list[dict]:
        result = []
        for m in matches:
            if (m.status or "").strip().upper() not in _FINISHED:
                continue
            if m.home_team != team and m.away_team != team:
                continue
            result.append({
                "home_team": m.home_team,
                "away_team": m.away_team,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "status": m.status,
            })
        return result

    def team_signal(team: str, standing_row) -> dict:
        sig: dict = {}
        inj = build_injury_signal(injuries_json, team)
        if inj:
            sig["injuries"] = inj
        form = build_form_signal(finished_for(team), team)
        if form:
            sig["form"] = form["form"]
        strength = build_strength_signal(
            team,
            fifa_rank=get_fifa_rank(team),
            standing_row=standing_row,
            top_scorers=scorers_by_team.get(team, []),
            marquee_players=get_marquee_players(team),
        )
        if strength:
            sig["strength"] = strength
        return sig

    return {
        "home": team_signal(home_team, home_row),
        "away": team_signal(away_team, away_row),
    }


def _signals_or_none(signals: dict) -> dict | None:
    """Return signals dict only when at least one side has content, else None."""
    if any(signals.get(side) for side in ("home", "away")):
        return signals
    return None


def backfill_forecasts(
    session_factory, matches: list, group_tables: dict, force_ids: set | None = None
) -> int:
    """Generate + store a pre-kickoff forecast for group-stage and knockout matches
    that have none yet. Keep-last-good: a failed/empty generation never overwrites a
    stored forecast. Any failure is logged and skipped — never aborts the collect.
    Skipped entirely when no DEEPSEEK_API_KEY is configured. Returns the count
    stored.

    Group-stage matches use each team's row from their shared group. Knockout
    matches resolve each team's final group-stage row by searching across all
    groups; if either team's row can't be found, that match is skipped gracefully."""
    if not settings.DEEPSEEK_API_KEY:
        return 0
    from app.api.fixtures import select_fixtures_needing_forecast
    from app.pipeline.forecast import (
        build_ko_forecast_facts,
        build_match_forecast_facts,
        generate_match_forecast,
    )

    with session_factory() as session:
        existing = {
            fid
            for (fid, forecast) in session.execute(
                select(matches_table.c.fixture_id, matches_table.c.forecast_json)
            ).all()
            if forecast
        }

    # Group-stage candidates (have group_name) + knockout candidates (no group_name).
    # select_fixtures_needing_forecast only returns group-stage matches, so we build
    # the KO candidate list separately.
    # force_ids are regenerated even if a forecast already exists (e.g. a manual
    # "refresh upcoming" run after a model change). keep-last-good still protects
    # them: a failed generation never overwrites the stored forecast.
    force_ids = force_ids or set()
    group_needing = set(select_fixtures_needing_forecast(matches, existing)) | {
        m.fixture_id for m in matches if m.group_name and m.fixture_id in force_ids
    }
    ko_needing = {
        m.fixture_id
        for m in matches
        if not m.group_name and (m.fixture_id not in existing or m.fixture_id in force_ids)
    }

    if not group_needing and not ko_needing:
        return 0

    to_store = []
    for m in matches:
        if m.fixture_id in group_needing:
            rows = group_tables.get(m.group_name or "", [])
            home_row = next((r for r in rows if r.team == m.home_team), None)
            away_row = next((r for r in rows if r.team == m.away_team), None)
            try:
                with session_factory() as session:
                    raw_signals = _build_forecast_signals(
                        session, m.home_team or "", m.away_team or "",
                        m.injuries_json, matches,
                        home_row=home_row, away_row=away_row,
                    )
                signals = _signals_or_none(raw_signals)
            except Exception as exc:
                log.warning("Signal assembly failed for %s: %s", m.fixture_id, exc)
                signals = None
            facts = build_match_forecast_facts(
                home_team=m.home_team,
                away_team=m.away_team,
                home_row=home_row,
                away_row=away_row,
                group_name=m.group_name,
                signals=signals,
            )
            if facts is None:
                continue
            try:
                result = generate_match_forecast(facts, prompt_variant="group")
            except Exception as exc:
                log.warning("Forecast generation failed for %s: %s", m.fixture_id, exc)
                continue
            if result:
                m.forecast_json, m.forecast_model = result
                m.forecast_kind = "group"
                to_store.append(m)

        elif m.fixture_id in ko_needing:
            home_row = _find_team_row_across_groups(group_tables, m.home_team or "")
            away_row = _find_team_row_across_groups(group_tables, m.away_team or "")
            if home_row is None or away_row is None:
                log.info(
                    "KO forecast skipped for fixture %s: group row missing "
                    "(home=%s found=%s, away=%s found=%s)",
                    m.fixture_id, m.home_team, home_row is not None,
                    m.away_team, away_row is not None,
                )
                continue
            try:
                with session_factory() as session:
                    raw_signals = _build_forecast_signals(
                        session, m.home_team or "", m.away_team or "",
                        m.injuries_json, matches,
                        home_row=home_row, away_row=away_row,
                    )
                signals = _signals_or_none(raw_signals)
            except Exception as exc:
                log.warning("Signal assembly failed for KO %s: %s", m.fixture_id, exc)
                signals = None
            facts = build_ko_forecast_facts(
                home_team=m.home_team,
                away_team=m.away_team,
                home_row=home_row,
                away_row=away_row,
                signals=signals,
            )
            if facts is None:
                continue
            try:
                result = generate_match_forecast(facts, prompt_variant="ko")
            except Exception as exc:
                log.warning("KO forecast generation failed for %s: %s", m.fixture_id, exc)
                continue
            if result:
                m.forecast_json, m.forecast_model = result
                m.forecast_kind = "ko"
                to_store.append(m)

    if to_store:
        with session_factory() as session:
            upsert_matches(session, to_store)
    log.info("Backfilled forecasts for %d matches", len(to_store))
    return len(to_store)


def backfill_social_highlights(session_factory, matches: list) -> int:
    """Collect + curate fan-discussion highlights for upcoming group-stage matches
    in the near-kickoff window. Unlike the once-only forecast backfill this REFRESHES
    daily (select_fixtures_needing_social keeps already-populated fixtures), bounded
    to SOCIAL_MAX_FIXTURES_PER_RUN to cap the daily fan-out. Keep-last-good: an empty/
    failed curation never overwrites stored highlights. Any failure is logged and
    skipped — never aborts the collect. Skipped entirely when no social source is
    available or no DEEPSEEK_API_KEY. Returns the count stored."""
    from datetime import datetime, timezone

    from app.api.fixtures import select_fixtures_needing_social
    from app.social import dedupe, pretrim
    from app.social.bluesky import BlueskySource
    from app.social.news import NewsSource
    from app.social.reddit import RedditSource
    from app.social.select import generate_social_highlights
    from app.social.x_ingest import load_x_candidates

    now = datetime.now(tz=timezone.utc)
    sources = [s for s in (RedditSource(), BlueskySource(), NewsSource()) if s.available()]
    # X posts are pre-collected out-of-band (paid API), keyed by fixture id.
    x_by_fixture = load_x_candidates(
        settings.SOCIAL_X_CANDIDATES_FILE, now=now, max_age_hours=settings.SOCIAL_X_MAX_AGE_HOURS
    )
    if (not sources and not x_by_fixture) or not settings.DEEPSEEK_API_KEY:
        return 0
    needing = set(select_fixtures_needing_social(matches, now))
    if not needing:
        return 0

    from datetime import timedelta
    since = now - timedelta(hours=settings.SOCIAL_LOOKBACK_HOURS)
    to_store = []
    for m in matches:
        if m.fixture_id not in needing or not m.home_team or not m.away_team:
            continue
        candidates = list(x_by_fixture.get(m.fixture_id, []))  # pre-collected X posts
        for src in sources:
            try:
                candidates.extend(src.fetch(m.home_team, m.away_team, since))
            except Exception as exc:  # noqa: BLE001 — one source down ≠ skip the fixture
                log.warning("Social source %s failed for %s: %s", src.name, m.fixture_id, exc)
        candidates = pretrim(dedupe(candidates), settings.SOCIAL_CANDIDATE_CAP)
        if not candidates:
            continue
        try:
            result = generate_social_highlights(m.home_team, m.away_team, candidates)
        except Exception as exc:  # noqa: BLE001 — keep-last-good on failure
            log.warning("Social curation failed for %s: %s", m.fixture_id, exc)
            continue
        if result:
            m.social_json, m.social_model = result
            to_store.append(m)
    if to_store:
        with session_factory() as session:
            upsert_matches(session, to_store)
    log.info("Backfilled social highlights for %d matches", len(to_store))
    return len(to_store)


def refresh_upcoming_forecasts() -> int:
    """Re-forecast every upcoming (not-yet-played) match with the current model.

    Loads matches + group tables from the DB only — NO API-Football calls — and
    force-regenerates forecasts for upcoming fixtures so a model change (new
    signals, tuned prompt) is reflected without waiting for the daily collect or
    clearing rows by hand. Played matches are never touched; keep-last-good means
    a failed generation leaves the existing forecast intact."""
    from datetime import datetime, timezone

    from app.data.models import Match
    from app.data.standings_math import compute_group_table, qualification_status

    if not settings.DEEPSEEK_API_KEY:
        log.error("DEEPSEEK_API_KEY not set — cannot refresh forecasts")
        return 1

    session_factory = make_session_factory()
    cols = [
        "fixture_id", "group_name", "home_team", "away_team", "home_score",
        "away_score", "status", "kickoff_utc", "stage", "injuries_json",
        "forecast_json", "forecast_model", "forecast_kind",
    ]
    with session_factory() as session:
        rows = session.execute(select(matches_table)).mappings().all()
    matches = [Match(**{c: r.get(c) for c in cols}) for r in rows]

    now = datetime.now(tz=timezone.utc)
    force_ids = {
        m.fixture_id
        for m in matches
        if (m.status or "").strip().upper() not in _FINISHED_FIXTURE_STATUSES
        and m.kickoff_utc is not None
        and m.kickoff_utc >= now
    }
    log.info("Refreshing forecasts for %d upcoming matches", len(force_ids))

    by_group: dict[str, list] = defaultdict(list)
    for m in matches:
        if m.group_name:
            by_group[m.group_name].append(m)
    group_tables = {g: compute_group_table(ms) for g, ms in by_group.items()}
    qual = qualification_status(group_tables)
    for grp_rows in group_tables.values():
        for row in grp_rows:
            row.qualification = qual.get(row.team)

    n = backfill_forecasts(session_factory, matches, group_tables, force_ids=force_ids)
    log.info("Refreshed %d upcoming forecasts", n)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect WC 2026 data for a date")
    parser.add_argument("--date", type=_parse_date, help="YYYY-MM-DD")
    parser.add_argument(
        "--refresh-upcoming-forecasts",
        action="store_true",
        help="Re-forecast upcoming matches with the current model (no API fetch); "
        "ignores --date",
    )
    args = parser.parse_args()
    if not args.refresh_upcoming_forecasts and args.date is None:
        parser.error("--date is required unless --refresh-upcoming-forecasts is set")

    from app.logging_config import configure_logging, stop_logging

    configure_logging()
    try:
        rc = (
            refresh_upcoming_forecasts()
            if args.refresh_upcoming_forecasts
            else run(args.date)
        )
    finally:
        stop_logging()  # flush before this short-lived process exits
    sys.exit(rc)


if __name__ == "__main__":
    main()
