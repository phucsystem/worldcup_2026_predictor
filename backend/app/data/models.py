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
    kickoff_utc: Optional[datetime]
    events: Optional[list[dict]] = None


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
