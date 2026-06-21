import re
from datetime import date, datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.data.models import Match, StandingRow, Team, TopScorer
from app.data.source import DataSource

# WC 2026 identifiers on API-Football
WC_LEAGUE_ID: int = 1
WC_SEASON: int = 2026

# Known status strings that mean "no score yet"
_NOT_STARTED = {"NS", "TBD", "PST", "CANC", "SUSP", "ABD", "AWD", "WO"}

# A real group label is "Group A".."Group L". The standings payload also carries
# an aggregate "Group Stage" block (the same teams again) which must NOT be
# treated as a group — it would overwrite teams' real group assignments.
_REAL_GROUP = re.compile(r"^Group [A-Z]$")


def _is_real_group(label: str | None) -> bool:
    return bool(label) and bool(_REAL_GROUP.match(label))


def parse_teams_from_standings(data: dict) -> list[Team]:
    """Extract one `Team` per national side from a /standings payload, keeping
    its real group label. Pure (no I/O) so the aggregate-block handling is
    unit-tested. Order-independent: a real `Group X` label always wins over the
    generic aggregate, regardless of which block appears first."""
    by_id: dict[int, Team] = {}
    for league_block in data.get("response", []):
        for group in league_block.get("league", {}).get("standings", []):
            for entry in group:
                team = entry.get("team", {})
                name = team.get("name")
                team_id = team.get("id")
                if not name or team_id is None:
                    continue
                real_group = entry.get("group") if _is_real_group(entry.get("group")) else None
                existing = by_id.get(team_id)
                if existing is None:
                    by_id[team_id] = Team(
                        team_id=team_id,
                        name=name,
                        logo_url=team.get("logo"),
                        group_name=real_group,
                    )
                    continue
                # Merge duplicates: prefer a real group; never let the aggregate clobber it.
                if real_group and not _is_real_group(existing.group_name):
                    existing.group_name = real_group
                if not existing.logo_url:
                    existing.logo_url = team.get("logo")
    return list(by_id.values())


def _parse_score(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _map_fixture(raw: dict) -> Match:
    fixture = raw.get("fixture", {})
    goals = raw.get("goals", {})
    status_obj = fixture.get("status", {})
    status = status_obj.get("short", "NS")
    teams = raw.get("teams", {})

    kickoff_raw = fixture.get("date")
    kickoff_utc: datetime | None = None
    if kickoff_raw:
        try:
            kickoff_utc = datetime.fromisoformat(kickoff_raw.replace("Z", "+00:00"))
        except ValueError:
            pass

    in_play_or_done = status not in _NOT_STARTED
    home_score = _parse_score(goals.get("home")) if in_play_or_done else None
    away_score = _parse_score(goals.get("away")) if in_play_or_done else None

    return Match(
        fixture_id=fixture.get("id", 0),
        # group_name is assigned by the collector from the standings team->group
        # map; the fixtures `league.round` is the matchday ("Group Stage - 1"),
        # NOT the group (A–L), so it must not be used here.
        group_name=None,
        home_team=teams.get("home", {}).get("name"),
        away_team=teams.get("away", {}).get("name"),
        home_score=home_score,
        away_score=away_score,
        status=status,
        elapsed=status_obj.get("elapsed"),
        kickoff_utc=kickoff_utc,
        events=None,
        stage=raw.get("league", {}).get("round"),
    )


def _map_standing_row(raw: dict, group_name: str) -> StandingRow:
    team = raw.get("team", {}).get("name", "")
    all_stats = raw.get("all", {})
    goals = all_stats.get("goals", {})
    gf = goals.get("for") or 0
    ga = goals.get("against") or 0
    return StandingRow(
        group_name=group_name,
        team=team,
        played=all_stats.get("played") or 0,
        won=all_stats.get("win") or 0,
        drawn=all_stats.get("draw") or 0,
        lost=all_stats.get("lose") or 0,
        gf=gf,
        ga=ga,
        gd=gf - ga,
        points=raw.get("points") or 0,
        position=raw.get("rank"),
    )


class APIFootballClient(DataSource):
    def __init__(
        self,
        league_id: int | None = None,
        season: int | None = None,
    ) -> None:
        self._league_id = league_id if league_id is not None else settings.API_FOOTBALL_LEAGUE
        self._season = season if season is not None else settings.API_FOOTBALL_SEASON
        self._base_url = settings.API_FOOTBALL_BASE_URL
        self._headers = {
            "x-apisports-key": settings.API_FOOTBALL_KEY or "",
        }

    def _get(self, path: str, params: dict) -> dict:
        with httpx.Client(base_url=self._base_url, headers=self._headers, timeout=15) as client:
            resp = client.get(path, params=params)
            resp.raise_for_status()
            data = resp.json()
        # API-Football returns HTTP 200 with a populated `errors` object on
        # plan/quota/parameter problems — surface it instead of silently
        # returning an empty response (e.g. "Free plans do not have access...").
        errors = data.get("errors")
        if errors:
            raise RuntimeError(f"API-Football error for {path}: {errors}")
        return data

    def get_fixtures(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        live: bool = False,
    ) -> list[Match]:
        """Fetch fixtures. With no date window, returns ALL fixtures for the
        league+season (the tournament-to-date set used to compute standings).
        With live=True, requests only in-play fixtures (`?live=all`) in a single
        call — used by the lightweight live poller."""
        params: dict = {"league": self._league_id, "season": self._season}
        if live:
            params["live"] = "all"
        if date_from:
            params["from"] = date_from.isoformat()
        if date_to:
            params["to"] = date_to.isoformat()
        data = self._get("/fixtures", params)
        return [_map_fixture(r) for r in data.get("response", [])]

    def _standings_response(self) -> dict:
        return self._get(
            "/standings",
            {"league": self._league_id, "season": self._season},
        )

    def get_teams(self) -> list[Team]:
        """National team metadata (id, name, crest logo, group) from the
        standings payload — no extra API call beyond the standings fetch. Group
        membership is structural; table NUMBERS stay Python-computed from results."""
        return parse_teams_from_standings(self._standings_response())

    def get_top_scorers(self) -> list[TopScorer]:
        """Tournament top scorers (1 API call). Free plan: season 2022."""
        data = self._get(
            "/players/topscorers",
            {"league": self._league_id, "season": self._season},
        )
        scorers: list[TopScorer] = []
        for entry in data.get("response", []):
            player = entry.get("player", {})
            player_id = player.get("id")
            if not player_id:
                continue  # player_id is half the unique key; skip rather than collapse to 0
            stats = entry.get("statistics") or [{}]
            first = stats[0] if stats else {}
            goals = (first.get("goals") or {}).get("total")
            scorers.append(
                TopScorer(
                    player_id=player_id,
                    name=player.get("name", ""),
                    photo_url=player.get("photo"),
                    team=(first.get("team") or {}).get("name"),
                    goals=goals or 0,
                )
            )
        return scorers

    def get_standings(self) -> list[StandingRow]:
        rows: list[StandingRow] = []
        for league_block in self._standings_response().get("response", []):
            for group in league_block.get("league", {}).get("standings", []):
                # group is a list of team rows; group name comes from each entry's "group".
                # Skip the aggregate "Group Stage" block — only real groups (A–L).
                for entry in group:
                    group_name = entry.get("group", "")
                    if not _is_real_group(group_name):
                        continue
                    rows.append(_map_standing_row(entry, group_name))
        return rows

    def get_events(self, fixture_id: int) -> list[dict]:
        data = self._get("/fixtures/events", {"fixture": fixture_id})
        return data.get("response", [])

    def get_fixture_statistics(self, fixture_id: int) -> list[dict]:
        """Per-team match statistics (possession, shots, xG, corners, …). Returns
        the raw response list (one entry per team); interpretation/shaping happens
        in the API layer (app.api.fixtures.normalize_statistics)."""
        data = self._get("/fixtures/statistics", {"fixture": fixture_id})
        return data.get("response", [])
