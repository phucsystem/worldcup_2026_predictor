from datetime import date, datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.data.models import Match, StandingRow
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

    league = raw.get("league", {})

    return Match(
        fixture_id=fixture.get("id", 0),
        group_name=league.get("round"),
        home_team=teams.get("home", {}).get("name"),
        away_team=teams.get("away", {}).get("name"),
        home_score=home_score,
        away_score=away_score,
        status=status,
        kickoff_utc=kickoff_utc,
        events=None,
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
        league_id: int = WC_LEAGUE_ID,
        season: int = WC_SEASON,
    ) -> None:
        self._league_id = league_id
        self._season = season
        self._base_url = settings.API_FOOTBALL_BASE_URL
        self._headers = {
            "x-apisports-key": settings.API_FOOTBALL_KEY or "",
        }

    def _get(self, path: str, params: dict) -> dict:
        with httpx.Client(base_url=self._base_url, headers=self._headers, timeout=15) as client:
            resp = client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()

    def get_fixtures(self, date_from: date, date_to: date) -> list[Match]:
        data = self._get(
            "/fixtures",
            {
                "league": self._league_id,
                "season": self._season,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
        )
        return [_map_fixture(r) for r in data.get("response", [])]

    def get_standings(self) -> list[StandingRow]:
        data = self._get(
            "/standings",
            {"league": self._league_id, "season": self._season},
        )
        rows: list[StandingRow] = []
        for league_block in data.get("response", []):
            for group in league_block.get("league", {}).get("standings", []):
                # group is a list of team rows; group name comes from first entry's "group"
                for entry in group:
                    group_name = entry.get("group", "")
                    rows.append(_map_standing_row(entry, group_name))
        return rows

    def get_events(self, fixture_id: int) -> list[dict]:
        data = self._get("/fixtures/events", {"fixture": fixture_id})
        return data.get("response", [])
