from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Match(BaseModel):
    fixture_id: int
    group_name: Optional[str]
    home_team: Optional[str]
    away_team: Optional[str]
    home_score: Optional[int]
    away_score: Optional[int]
    status: Optional[str]
    # Live match minute from API-Football (fixture.status.elapsed); None when not in play.
    elapsed: Optional[int] = None
    kickoff_utc: Optional[datetime]
    events: Optional[list[dict]] = None
    # Raw API-Football /fixtures/statistics response (per-team stat arrays).
    # Populated once on the daily backfill for finished matches; None otherwise.
    statistics: Optional[list[dict]] = None
    # DeepSeek-narrated one-line verdict + the model that produced it. Populated
    # by the verdict pipeline on the daily backfill; None until then.
    verdict_text: Optional[str] = None
    verdict_model: Optional[str] = None
    # Raw competition round, e.g. "Group Stage - 1" or "Round of 16". Used to
    # distinguish group-stage matches (which count toward group tables) from
    # knockout matches, and persisted so the knockout bracket can group by round.
    stage: Optional[str] = None


class StandingRow(BaseModel):
    group_name: str
    team: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    gf: int = 0
    ga: int = 0
    gd: int = 0
    points: int = 0
    position: Optional[int] = None
    prev_position: Optional[int] = None
    qualification: Optional[str] = None


class MatchResult(BaseModel):
    """Outcome of a single completed match from one team's perspective."""
    team: str
    opponent: str
    goals_for: int
    goals_against: int
    won: bool
    drawn: bool
    lost: bool


class Team(BaseModel):
    """National team metadata extracted from the standings payload (no extra
    API call). `logo_url` is the national crest, usable as a flag."""
    team_id: int
    name: str
    logo_url: Optional[str] = None
    group_name: Optional[str] = None


class TopScorer(BaseModel):
    player_id: int
    name: str
    photo_url: Optional[str] = None
    team: Optional[str] = None
    goals: int = 0
