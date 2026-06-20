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

    def get_fixtures(self, date_from: date | None = None, date_to: date | None = None) -> list[Match]:
        """Fetch fixtures. With no date window, returns ALL fixtures for the
        league+season (the tournament-to-date set used to compute standings)."""
        params: dict = {"league": self._league_id, "season": self._season}
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
        teams: list[Team] = []
        for league_block in self._standings_response().get("response", []):
            for group in league_block.get("league", {}).get("standings", []):
                for entry in group:
                    team = entry.get("team", {})
                    name = team.get("name")
                    team_id = team.get("id")
                    # Skip rows missing an id/name: team_id is the PK, so coalescing
                    # to 0 would silently collapse multiple teams onto one row.
                    if not name or not team_id:
                        continue
                    teams.append(
                        Team(
                            team_id=team_id,
                            name=name,
                            logo_url=team.get("logo"),
                            group_name=entry.get("group"),
                        )
                    )
        return teams

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
                # group is a list of team rows; group name comes from each entry's "group"
                for entry in group:
                    group_name = entry.get("group", "")
                    rows.append(_map_standing_row(entry, group_name))
        return rows

    def get_events(self, fixture_id: int) -> list[dict]:
        data = self._get("/fixtures/events", {"fixture": fixture_id})
        return data.get("response", [])
