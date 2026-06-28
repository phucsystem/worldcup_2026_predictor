"""Read-only fixtures + stars API: upcoming fixtures (day-grouped), the knockout
bracket, and tournament top scorers. Shaping logic is split into pure functions
(no DB/network) so it can be unit-tested directly.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy import select

from app.config import settings
from app.data.availability import build_team_status, last_match_contributors
from app.data.fifa_rankings import get_fifa_rank
from app.data.models import Match, StandingRow, TeamStatus
from app.data.repository import (
    finished_group_matches_for_team,
    make_engine,
    make_session_factory,
    matches_table,
    teams_table,
    top_scorers_table,
)
from app.data.standings_math import compute_group_table

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])

_engine = None

# Knockout rounds in bracket order. Matching is case-insensitive on the raw
# API-Football `round` string; anything unrecognised sorts after these.
KNOCKOUT_ROUND_ORDER = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "3rd Place Final",
    "Final",
]
_KNOCKOUT_ORDER_INDEX = {name.lower(): i for i, name in enumerate(KNOCKOUT_ROUND_ORDER)}

# API-Football short status codes for an in-play match (excludes NS and any
# finished/postponed state). Drives the /live endpoint and the live poller.
LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE"}

# Finished short status codes — drive the once-only events backfill on the daily
# collect path.
FINISHED_STATUSES = {"FT", "AET", "PEN"}

# ---------------------------------------------------------------------------
# WC 2026 knockout bracket map. The feed exposes no match number and no
# pairing, so Round-of-32 ties are anchored by team-set and every later round
# is derived from this fixed tree. Match numbers follow FIFA's published
# schedule (R32 = 73–88, R16 = 89–96, QF = 97–100, SF = 101–102, Final = 104).
# ---------------------------------------------------------------------------

# Match number -> the two team names of that Round-of-32 tie (exact feed names).
R32_MATCH_TEAMS: dict[int, frozenset] = {
    73: frozenset({"South Africa", "Canada"}),
    74: frozenset({"Germany", "Paraguay"}),
    75: frozenset({"Netherlands", "Morocco"}),
    76: frozenset({"Brazil", "Japan"}),
    77: frozenset({"France", "Sweden"}),
    78: frozenset({"Ivory Coast", "Norway"}),
    79: frozenset({"Mexico", "Ecuador"}),
    80: frozenset({"England", "Congo DR"}),
    81: frozenset({"USA", "Bosnia & Herzegovina"}),
    82: frozenset({"Belgium", "Senegal"}),
    83: frozenset({"Portugal", "Croatia"}),
    84: frozenset({"Spain", "Austria"}),
    85: frozenset({"Switzerland", "Algeria"}),
    86: frozenset({"Argentina", "Cape Verde Islands"}),
    87: frozenset({"Colombia", "Ghana"}),
    88: frozenset({"Australia", "Egypt"}),
}

# Later-round match number -> (feeder match A, feeder match B). The winners of
# A and B become the home/away of this tie.
KNOCKOUT_FEEDERS: dict[int, tuple] = {
    89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
    93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87),
    97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96),
    101: (97, 98), 102: (99, 100),
    104: (101, 102),
}

# Round label -> ordered match numbers, laid out so each adjacent pair feeds the
# next round's tie (the frontend draws connectors by adjacency).
KNOCKOUT_ROUND_SLOTS: list = [
    ("Round of 32", [74, 77, 73, 75, 83, 84, 81, 82, 76, 78, 79, 80, 86, 88, 85, 87]),
    ("Round of 16", [89, 90, 93, 94, 91, 92, 95, 96]),
    ("Quarter-finals", [97, 98, 99, 100]),
    ("Semi-finals", [101, 102]),
    ("Final", [104]),
]


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class FixtureRow(BaseModel):
    fixture_id: int
    home_team: Optional[str]
    away_team: Optional[str]
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None
    elapsed: Optional[int] = None
    stage: Optional[str] = None
    group_name: Optional[str] = None
    kickoff_utc: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MatchEvent(BaseModel):
    minute: int
    extra: Optional[int] = None
    type: Optional[str] = None
    detail: Optional[str] = None
    player: Optional[str] = None
    assist: Optional[str] = None
    team: Optional[str] = None
    side: Optional[str] = None  # "home" | "away" | None


class MatchStat(BaseModel):
    label: str
    # Display strings preserve API formatting ("58%", "2.90", "18").
    home: str
    away: str
    # Bar widths 0-100 (sum to 100 unless both values are 0). Computed in Python.
    home_pct: float
    away_pct: float


class ForecastFactor(BaseModel):
    name: str
    lean: str  # "home" | "away" | "even"
    why: str


class MatchForecast(BaseModel):
    # Integer win/draw/win split (sums to 100) + the factors driving it. Produced
    # by the forecast pipeline (app.pipeline.forecast); None on a fixture until
    # the backfill has run for it. `model` names the producing model.
    home_pct: int
    draw_pct: int
    away_pct: int
    factors: list[ForecastFactor] = []
    model: Optional[str] = None


class SocialHighlight(BaseModel):
    # One curated fan comment. All fields originate from the fetched source post
    # (app.social); the model only selects which candidates surface + the `why`
    # tag. `url` is always an http(s) link back to the source for attribution.
    source: str          # "reddit" | "bluesky"
    url: str
    author: str
    posted_at: Optional[str] = None
    text: str
    why: Optional[str] = None


class MatchLiveWinProb(BaseModel):
    # Final hybrid live win/draw/loss split (Python base + bounded AI adjustment),
    # recomputed every poll for an in-play group-stage match. None until then.
    home: int
    draw: int
    away: int


class LiveWinProbPoint(BaseModel):
    # One point on the win-prob swing chart — captured per significant event, not
    # per poll. `label` names the trigger ("Goal · Brazil", "64'", "KO").
    minute: int
    home_pct: int
    draw_pct: int
    away_pct: int
    home_score: int
    away_score: int
    label: Optional[str] = None


class ForecastSignalsSide(BaseModel):
    fifa_rank: Optional[int] = None
    form: Optional[str] = None          # e.g. "WWDWL" — last 5, oldest-first
    goals_per_game: Optional[float] = None


class ForecastSignals(BaseModel):
    home: ForecastSignalsSide
    away: ForecastSignalsSide


class FixtureDetail(FixtureRow):
    events: list[MatchEvent] = []
    statistics: list[MatchStat] = []
    verdict: Optional[str] = None
    verdict_model: Optional[str] = None
    forecast: Optional[MatchForecast] = None
    forecast_signals: Optional[ForecastSignals] = None
    # Curated fan-discussion highlights for an upcoming fixture; empty list when
    # none stored. `social_model` names the producing model.
    social_highlights: list[SocialHighlight] = []
    social_model: Optional[str] = None
    # Hybrid live win-prob + swing-chart history + AI live read, populated on the
    # live-poll path for in-play group-stage matches; null/empty otherwise. The
    # internal stored adjustment (live_winprob_adj_json) is NOT exposed — the client
    # only ever needs the final split.
    live_winprob: Optional[MatchLiveWinProb] = None
    live_winprob_history: list[LiveWinProbPoint] = []
    live_read: Optional[str] = None
    live_read_model: Optional[str] = None
    # Per-team objective + availability, populated only for non-finished
    # fixtures (preview/live); None on finished fixtures and when a side has
    # nothing to show.
    home_status: Optional[TeamStatus] = None
    away_status: Optional[TeamStatus] = None


class FixtureDay(BaseModel):
    date: date
    fixtures: list[FixtureRow]


class UpcomingFixtures(BaseModel):
    up_next: Optional[FixtureRow]
    days: list[FixtureDay]


class KnockoutRound(BaseModel):
    round: str
    ties: list[FixtureRow]


class KnockoutBracket(BaseModel):
    rounds: list[KnockoutRound]


class StarRow(BaseModel):
    player_id: int
    name: str
    team: Optional[str]
    goals: int
    photo_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Pure shaping functions (no I/O — unit-tested in test_fixtures_shaping.py)
# ---------------------------------------------------------------------------

def is_knockout_stage(stage: Optional[str]) -> bool:
    return bool(stage) and stage.strip().lower() in _KNOCKOUT_ORDER_INDEX


def is_live_status(status: Optional[str]) -> bool:
    return bool(status) and status.strip().upper() in LIVE_STATUSES


def normalize_events(
    raw: Optional[list[dict]], home_team: Optional[str], away_team: Optional[str]
) -> list[MatchEvent]:
    """Map raw API-Football /fixtures/events entries to a stable, frontend-
    friendly shape. `side` is resolved by matching the event team name to the
    home/away team; the running timeline score is NOT computed here (the frontend
    derives it from goal events in Phase 2)."""
    if not raw:
        return []
    events: list[MatchEvent] = []
    for e in raw:
        time = e.get("time") or {}
        team = (e.get("team") or {}).get("name")
        if team and team == home_team:
            side = "home"
        elif team and team == away_team:
            side = "away"
        else:
            side = None
        events.append(
            MatchEvent(
                minute=time.get("elapsed") or 0,
                extra=time.get("extra"),
                type=e.get("type"),
                detail=e.get("detail"),
                player=(e.get("player") or {}).get("name"),
                assist=(e.get("assist") or {}).get("name"),
                team=team,
                side=side,
            )
        )
    return events


def _finished_fixtures_missing(matches, existing: set[int]) -> list[int]:
    """Finished fixture ids absent from `existing` — the once-only daily-backfill
    set shared by the events and statistics backfills. Live matches are handled by
    the live poller, not here, so they are skipped."""
    return [
        m.fixture_id
        for m in matches
        if (m.status or "").strip().upper() in FINISHED_STATUSES
        and m.fixture_id not in existing
    ]


# API-Football stat `type` → prototype S-10 label, in display order. A type absent
# from the payload is simply skipped (no zero-fill).
_STAT_LABELS: list[tuple[str, str]] = [
    ("Ball Possession", "Possession"),
    ("Total Shots", "Shots"),
    ("Shots on Goal", "Shots on target"),
    ("expected_goals", "Expected goals (xG)"),
    ("Corner Kicks", "Corners"),
]


def _stat_number(value) -> float:
    """Numeric magnitude of a stat value for bar widths. Strips '%', tolerates
    None/blank/non-numeric → 0.0."""
    if value is None:
        return 0.0
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        return 0.0


def _stat_display(value) -> str:
    return "0" if value is None else str(value)


def normalize_statistics(
    raw: Optional[list[dict]], home_team: Optional[str], away_team: Optional[str]
) -> list[MatchStat]:
    """Map the raw /fixtures/statistics response (one entry per team) to ordered
    MatchStat bars. Teams are matched by name (falling back to payload order);
    stat types absent from the payload are omitted; bar percentages are computed
    here (deterministic) — never fabricated."""
    if not raw:
        return []

    def stats_of(entry: dict) -> dict:
        return {s.get("type"): s.get("value") for s in (entry.get("statistics") or [])}

    by_team = {(e.get("team") or {}).get("name"): stats_of(e) for e in raw}
    home_stats = by_team.get(home_team)
    away_stats = by_team.get(away_team)
    # Fall back to payload order if EITHER side failed to match by name — a
    # one-sided match would otherwise zero-fill the unmatched team's bars (a
    # fabricated-looking "0" for a team that actually had data).
    if (home_stats is None or away_stats is None) and len(raw) >= 2:
        home_stats, away_stats = stats_of(raw[0]), stats_of(raw[1])
    home_stats = home_stats or {}
    away_stats = away_stats or {}

    out: list[MatchStat] = []
    for api_type, label in _STAT_LABELS:
        hv = home_stats.get(api_type)
        av = away_stats.get(api_type)
        if hv is None and av is None:
            continue
        hn, an = _stat_number(hv), _stat_number(av)
        total = hn + an
        if total > 0:
            home_pct = round(hn / total * 100, 1)
            away_pct = round(100 - home_pct, 1)
        else:
            home_pct = away_pct = 0.0
        out.append(
            MatchStat(
                label=label,
                home=_stat_display(hv),
                away=_stat_display(av),
                home_pct=home_pct,
                away_pct=away_pct,
            )
        )
    return out


def _safe_live_winprob(blob) -> Optional["MatchLiveWinProb"]:
    """Map a stored live_winprob_json blob to MatchLiveWinProb, degrading a
    malformed blob to None rather than 500-ing the fixture."""
    if not blob:
        return None
    try:
        return MatchLiveWinProb(home=blob["home"], draw=blob["draw"], away=blob["away"])
    except (TypeError, KeyError, ValueError):
        return None


def _safe_live_winprob_history(blob) -> list["LiveWinProbPoint"]:
    """Map the stored history series to LiveWinProbPoint, dropping any malformed
    point rather than failing the whole fixture."""
    if not isinstance(blob, list):
        return []
    points: list[LiveWinProbPoint] = []
    for p in blob:
        try:
            points.append(LiveWinProbPoint(
                minute=p["minute"],
                home_pct=p["home_pct"], draw_pct=p["draw_pct"], away_pct=p["away_pct"],
                home_score=p["home_score"], away_score=p["away_score"],
                label=p.get("label"),
            ))
        except (TypeError, KeyError, ValueError, AttributeError):
            continue
    return points


def select_fixtures_needing_events(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored events yet. `existing` is
    the set of fixture ids that already have events."""
    return _finished_fixtures_missing(matches, existing)


def select_fixtures_needing_statistics(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored statistics yet. `existing`
    is the set of fixture ids that already have statistics."""
    return _finished_fixtures_missing(matches, existing)


def select_fixtures_needing_verdict(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored verdict yet. `existing` is
    the set of fixture ids that already have a verdict."""
    return _finished_fixtures_missing(matches, existing)


def select_fixtures_needing_forecast(matches, existing: set[int]) -> list[int]:
    """Fixture ids for group-stage matches with no stored forecast yet. `existing`
    is the set of fixture ids that already have one. Knockout matches are skipped
    — a forecast is grounded in group standings, which they lack."""
    return [
        m.fixture_id
        for m in matches
        if m.fixture_id not in existing and m.group_name
    ]


def select_fixtures_needing_social(matches, now: datetime) -> list[int]:
    """Fixture ids for upcoming group-stage matches whose social highlights should
    be (re)collected. Unlike the once-only forecast selector this is REFRESH-AWARE:
    it deliberately does NOT exclude fixtures that already have highlights, so buzz
    re-curates daily as kickoff approaches. Bounded to keep the daily fan-out sane:
    only non-finished group-stage fixtures kicking off within
    SOCIAL_LOOKAHEAD_HOURS, sorted by nearest kickoff, capped at
    SOCIAL_MAX_FIXTURES_PER_RUN. Pure: `now` is passed in, not read from the clock."""
    horizon = now + timedelta(hours=settings.SOCIAL_LOOKAHEAD_HOURS)
    upcoming = [
        m
        for m in matches
        if m.group_name
        and (m.status or "").strip().upper() not in FINISHED_STATUSES
        and m.kickoff_utc is not None
        and now <= m.kickoff_utc <= horizon
    ]
    upcoming.sort(key=lambda m: m.kickoff_utc)
    return [m.fixture_id for m in upcoming[: settings.SOCIAL_MAX_FIXTURES_PER_RUN]]


def _team_forecast_signals(session, team: str) -> ForecastSignalsSide:
    """Compute FIFA rank, last-5 form string, and goals/game for `team` from
    finished group-stage matches. Returns a ForecastSignalsSide with whatever
    data is available; missing data fields stay None."""
    rank = get_fifa_rank(team)
    matches = finished_group_matches_for_team(session, team)

    form: Optional[str] = None
    goals_per_game: Optional[float] = None

    if matches:
        letters = []
        total_gf = 0
        for m in matches:
            is_home = m["home_team"] == team
            gf = (m["home_score"] if is_home else m["away_score"]) or 0
            ga = (m["away_score"] if is_home else m["home_score"]) or 0
            total_gf += gf
            if gf > ga:
                letters.append("W")
            elif gf == ga:
                letters.append("D")
            else:
                letters.append("L")
        # last 5, oldest-first (matches are already sorted by kickoff_utc asc)
        form = "".join(letters[-5:])
        n = len(matches)
        goals_per_game = round(total_gf / n, 2) if n else None

    return ForecastSignalsSide(fifa_rank=rank, form=form, goals_per_game=goals_per_game)


def _compute_forecast_signals(session, home_team: Optional[str], away_team: Optional[str]) -> Optional[ForecastSignals]:
    """Build ForecastSignals for both sides. Returns None when both teams are
    unknown (no rank, no matches) — avoids a meaningless empty object."""
    if not home_team and not away_team:
        return None
    home_side = _team_forecast_signals(session, home_team or "")
    away_side = _team_forecast_signals(session, away_team or "")
    # At least one signal must be populated for the object to be meaningful
    has_data = any([
        home_side.fifa_rank, home_side.form, home_side.goals_per_game,
        away_side.fifa_rank, away_side.form, away_side.goals_per_game,
    ])
    return ForecastSignals(home=home_side, away=away_side) if has_data else None


def _enrich(row: dict, logos: dict[str, str]) -> FixtureRow:
    return FixtureRow(
        fixture_id=row["fixture_id"],
        home_team=row.get("home_team"),
        away_team=row.get("away_team"),
        home_logo=logos.get(row.get("home_team")),
        away_logo=logos.get(row.get("away_team")),
        home_score=row.get("home_score"),
        away_score=row.get("away_score"),
        status=row.get("status"),
        elapsed=row.get("elapsed"),
        stage=row.get("stage"),
        group_name=row.get("group_name"),
        kickoff_utc=row.get("kickoff_utc"),
        updated_at=row.get("updated_at"),
    )


def shape_upcoming(rows: list[dict], logos: dict[str, str]) -> UpcomingFixtures:
    """Group upcoming fixtures by kickoff day (ascending) and surface the soonest
    as `up_next`. Rows are assumed already filtered to upcoming matches."""
    enriched = sorted(
        (_enrich(r, logos) for r in rows),
        key=lambda f: (f.kickoff_utc is None, f.kickoff_utc),
    )
    # Bucket by the calendar day in the brief timezone, not UTC: a 17:00Z match
    # is the next morning in Australia/Melbourne, so UTC bucketing splits one
    # local matchday across two day headers and mislabels each.
    brief_tz = ZoneInfo(settings.BRIEF_TIMEZONE)
    by_day: dict[date, list[FixtureRow]] = {}
    day_order: list[date] = []
    for f in enriched:
        if f.kickoff_utc is None:
            continue
        ko = f.kickoff_utc
        if ko.tzinfo is None:
            ko = ko.replace(tzinfo=timezone.utc)
        day = ko.astimezone(brief_tz).date()
        if day not in by_day:
            by_day[day] = []
            day_order.append(day)
        by_day[day].append(f)

    days = [FixtureDay(date=d, fixtures=by_day[d]) for d in day_order]
    up_next = next((f for f in enriched if f.kickoff_utc is not None), None)
    return UpcomingFixtures(up_next=up_next, days=days)


def shape_live(rows: list[dict], logos: dict[str, str]) -> list[FixtureRow]:
    """Filter to in-play matches and return them soonest-kicked first. Pure
    (no DB/network) so the live filter + ordering is unit-tested."""
    live = [_enrich(r, logos) for r in rows if is_live_status(r.get("status"))]
    live.sort(key=lambda f: (f.kickoff_utc is None, f.kickoff_utc))
    return live


def _is_finished(status: Optional[str]) -> bool:
    return bool(status) and status.strip().upper() in FINISHED_STATUSES


def _winner_team(tie: Optional[FixtureRow]) -> Optional[str]:
    """Winning team of a finished tie by score; None if the tie is unplayed,
    in-play, or level (a penalty-shootout result isn't derivable from the
    90/120-minute score, so we leave the next slot TBD rather than guess)."""
    if tie is None or not _is_finished(tie.status):
        return None
    if tie.home_score is None or tie.away_score is None:
        return None
    if tie.home_score > tie.away_score:
        return tie.home_team
    if tie.away_score > tie.home_score:
        return tie.away_team
    return None


def _placeholder_tie(
    match_no: int, label: str, home: Optional[str], away: Optional[str],
    logos: dict[str, str],
) -> FixtureRow:
    """A synthesized (not-yet-played / not-in-feed) tie. The negative fixture_id
    marks it as derived so the frontend renders it without a match-analysis link."""
    return FixtureRow(
        fixture_id=-match_no,
        home_team=home,
        away_team=away,
        home_logo=logos.get(home) if home else None,
        away_logo=logos.get(away) if away else None,
        stage=label,
    )


def build_full_bracket(rows: list[dict], logos: dict[str, str]) -> KnockoutBracket:
    """Full end-to-end bracket: real Round-of-32 ties from the feed anchored to
    the FIFA bracket map by team-set, with every later round synthesized and
    winners propagated as ties finish. A real feed fixture for a later round
    overrides its synthesized slot (self-healing once the feed publishes it).
    Empty until any knockout tie exists."""
    ko_rows = [r for r in rows if is_knockout_stage(r.get("stage"))]
    if not ko_rows:
        return KnockoutBracket(rounds=[])

    by_teams: dict[frozenset, dict] = {
        frozenset({r.get("home_team"), r.get("away_team")}): r for r in ko_rows
    }
    label_by_match = {m: lbl for lbl, ms in KNOCKOUT_ROUND_SLOTS for m in ms}
    slot: dict[int, FixtureRow] = {}

    # Round of 32 (73–88): real feed tie matched by team-set, else TBD placeholder.
    for n, teams in R32_MATCH_TEAMS.items():
        feed = by_teams.get(teams)
        slot[n] = _enrich(feed, logos) if feed is not None else _placeholder_tie(
            n, "Round of 32", None, None, logos
        )

    # Later rounds (89–104): propagate winners up the fixed tree; prefer a real
    # feed fixture for a slot when its two resolved teams already exist in the feed.
    for n in range(89, 105):
        if n not in KNOCKOUT_FEEDERS:
            continue
        a, b = KNOCKOUT_FEEDERS[n]
        home = _winner_team(slot.get(a))
        away = _winner_team(slot.get(b))
        feed = by_teams.get(frozenset({home, away})) if home and away else None
        slot[n] = _enrich(feed, logos) if feed is not None else _placeholder_tie(
            n, label_by_match.get(n, ""), home, away, logos
        )

    rounds = [
        KnockoutRound(round=label, ties=[slot[n] for n in slots if n in slot])
        for label, slots in KNOCKOUT_ROUND_SLOTS
    ]
    return KnockoutBracket(rounds=[r for r in rounds if r.ties])


def shape_knockout(rows: list[dict], logos: dict[str, str]) -> KnockoutBracket:
    """Public entry: the full end-to-end knockout bracket (see build_full_bracket)."""
    return build_full_bracket(rows, logos)


# ---------------------------------------------------------------------------
# DB plumbing
# ---------------------------------------------------------------------------

def _logo_map(session) -> dict[str, str]:
    rows = session.execute(
        select(teams_table.c.name, teams_table.c.logo_url)
    ).fetchall()
    return {r.name: r.logo_url for r in rows if r.logo_url}


def _all_group_tables(session) -> dict[str, list[StandingRow]]:
    """Group-stage standings tables for every group, computed live from stored
    matches (mirrors tournament.py). Needed in full so qualification status can
    account for WC 2026 best-third advancement."""
    rows = session.execute(
        select(matches_table).where(matches_table.c.group_name.isnot(None))
    ).mappings().all()
    by_group: dict[str, list[Match]] = {}
    for r in rows:
        by_group.setdefault(r["group_name"], []).append(
            Match(
                fixture_id=r["fixture_id"],
                group_name=r["group_name"],
                home_team=r["home_team"],
                away_team=r["away_team"],
                home_score=r["home_score"],
                away_score=r["away_score"],
                status=r["status"],
                kickoff_utc=r["kickoff_utc"],
                stage=r["stage"],
            )
        )
    return {g: compute_group_table(ms) for g, ms in by_group.items()}


def _key_names_by_team(session) -> dict[str, set[str]]:
    """Tournament top-scorer names grouped by team — one half of the key-player
    set (the other half, last-match scorers/assisters, is per-fixture)."""
    rows = session.execute(
        select(top_scorers_table.c.name, top_scorers_table.c.team)
        .where(top_scorers_table.c.season == settings.API_FOOTBALL_SEASON)
    ).fetchall()
    by_team: dict[str, set[str]] = {}
    for r in rows:
        if r.name and r.team:
            by_team.setdefault(r.team, set()).add(r.name)
    return by_team


def _team_statuses(
    session,
    home_team: Optional[str],
    away_team: Optional[str],
    injury_records: list[dict],
) -> tuple[Optional[TeamStatus], Optional[TeamStatus]]:
    """Build (home_status, away_status) for a non-finished fixture. Each side
    gets its objective (from live group tables), availability (suspensions replayed
    from its prior group matches), and injured/doubtful players (from this fixture's
    stored /injuries records), with key players emphasised."""
    group_tables = _all_group_tables(session)
    top_scorers = _key_names_by_team(session)

    def side(team: Optional[str]) -> Optional[TeamStatus]:
        if not team:
            return None
        prior = finished_group_matches_for_team(session, team)
        key_names = top_scorers.get(team, set()) | last_match_contributors(prior, team)
        return build_team_status(
            group_tables, team, prior, key_names=key_names, injury_records=injury_records
        )

    return side(home_team), side(away_team)


def _row_to_dict(r) -> dict:
    return {
        "fixture_id": r.fixture_id,
        "home_team": r.home_team,
        "away_team": r.away_team,
        "home_score": r.home_score,
        "away_score": r.away_score,
        "status": r.status,
        "elapsed": r.elapsed,
        "stage": r.stage,
        "group_name": r.group_name,
        "kickoff_utc": r.kickoff_utc,
        "updated_at": r.updated_at,
    }


@router.get("/upcoming", response_model=UpcomingFixtures)
def get_upcoming():
    session = _get_session()
    try:
        now = datetime.now(tz=timezone.utc)
        rows = session.execute(
            select(matches_table)
            .where(matches_table.c.home_score.is_(None))
            .where(matches_table.c.kickoff_utc.isnot(None))
            .where(matches_table.c.kickoff_utc >= now)
            .order_by(matches_table.c.kickoff_utc)
        ).fetchall()
        logos = _logo_map(session)
    finally:
        session.close()
    return shape_upcoming([_row_to_dict(r) for r in rows], logos)


@router.get("/live", response_model=list[FixtureRow])
def get_live():
    """In-play matches, soonest-kicked first. Reads the DB only (the live poller
    refreshes scores/elapsed out-of-band), so this makes zero external calls.

    A finished match drops out of API-Football's ?live=all feed, so the live
    poller never writes its final FT status — only the full collect does. The
    kickoff-window guard keeps such a stale live row from rendering as "live"
    indefinitely between full collects."""
    session = _get_session()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=settings.LIVE_WINDOW_HOURS)
    try:
        rows = session.execute(
            select(matches_table)
            .where(matches_table.c.status.in_(LIVE_STATUSES))
            .where(matches_table.c.kickoff_utc >= cutoff)
            .order_by(matches_table.c.kickoff_utc)
        ).fetchall()
        logos = _logo_map(session)
    finally:
        session.close()
    return shape_live([_row_to_dict(r) for r in rows], logos)


@router.get("/knockout", response_model=KnockoutBracket)
def get_knockout():
    session = _get_session()
    try:
        rows = session.execute(
            select(matches_table)
            .where(matches_table.c.group_name.is_(None))
            .order_by(matches_table.c.kickoff_utc)
        ).fetchall()
        logos = _logo_map(session)
    finally:
        session.close()
    return shape_knockout([_row_to_dict(r) for r in rows], logos)


# Registered last so the literal routes (/upcoming, /live, /knockout) win over
# this int path param.
@router.get("/{fixture_id}", response_model=FixtureDetail)
def get_fixture(fixture_id: int):
    session = _get_session()
    try:
        row = session.execute(
            select(matches_table).where(matches_table.c.fixture_id == fixture_id)
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="fixture not found")
        logos = _logo_map(session)
        events_json = row.events_json
        statistics_json = row.statistics_json
        verdict_text = row.verdict_text
        verdict_model = row.verdict_model
        forecast_json = row.forecast_json
        forecast_model = row.forecast_model
        social_json = row.social_json
        social_model = row.social_model
        live_winprob_json = row.live_winprob_json
        live_winprob_history_json = row.live_winprob_history_json
        live_read_text = row.live_read_text
        live_read_model = row.live_read_model
        injuries_json = row.injuries_json
        home_team, away_team = row.home_team, row.away_team
        # Objective + availability are a pre-match aid: compute them for
        # preview/live fixtures only, never for a finished result.
        is_finished = (row.status or "").strip().upper() in FINISHED_STATUSES
        injury_records = (injuries_json or {}).get("players") if isinstance(injuries_json, dict) else None
        home_status, away_status = (
            (None, None) if is_finished
            else _team_statuses(session, home_team, away_team, injury_records or [])
        )
        # Compute key signals for the forecast column only when a forecast exists
        # (avoids unnecessary queries on every fixture; null-safe for non-group teams).
        forecast_signals = (
            _compute_forecast_signals(session, home_team, away_team)
            if forecast_json else None
        )
    finally:
        session.close()
    base = _enrich(_row_to_dict(row), logos)
    events = normalize_events(events_json, home_team, away_team)
    statistics = normalize_statistics(statistics_json, home_team, away_team)
    forecast = MatchForecast(**forecast_json, model=forecast_model) if forecast_json else None
    # Blobs are LLM-produced from the social backfill; tolerate a malformed item
    # by dropping it rather than 500-ing the whole fixture (degrade the panel, not
    # the page). `social_json` may be absent or not the expected dict shape.
    raw_highlights = (social_json or {}).get("highlights") if isinstance(social_json, dict) else None
    social_highlights = []
    for h in raw_highlights or []:
        try:
            social_highlights.append(SocialHighlight(**h))
        except (TypeError, ValidationError):
            continue
    live_winprob = _safe_live_winprob(live_winprob_json)
    live_winprob_history = _safe_live_winprob_history(live_winprob_history_json)
    return FixtureDetail(
        **base.model_dump(),
        events=events,
        statistics=statistics,
        verdict=verdict_text,
        verdict_model=verdict_model,
        forecast=forecast,
        forecast_signals=forecast_signals,
        social_highlights=social_highlights,
        social_model=social_model if social_highlights else None,
        live_winprob=live_winprob,
        live_winprob_history=live_winprob_history,
        live_read=live_read_text,
        live_read_model=live_read_model,
        home_status=home_status,
        away_status=away_status,
    )


# `/api/stars` lives logically with fixtures enrichment; exposed via its own
# router prefix so the URL stays `/api/stars` (not `/api/fixtures/stars`).
stars_router = APIRouter(prefix="/api/stars", tags=["stars"])


@stars_router.get("", response_model=list[StarRow])
def get_stars():
    session = _get_session()
    try:
        rows = session.execute(
            select(top_scorers_table)
            .where(top_scorers_table.c.season == settings.API_FOOTBALL_SEASON)
            .order_by(top_scorers_table.c.goals.desc())
        ).fetchall()
    finally:
        session.close()
    return [
        StarRow(
            player_id=r.player_id,
            name=r.name,
            team=r.team,
            goals=r.goals or 0,
            photo_url=r.photo_url,
        )
        for r in rows
    ]
