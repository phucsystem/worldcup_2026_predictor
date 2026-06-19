"""
Static seed data: WC 2026 group structure (12 groups × 4 teams).
Team names reflect the official draw held in December 2024.
Provides a zeroed standings skeleton so the site has structure before
the first live collector run.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.data.models import StandingRow
from app.data.repository import upsert_standings_snapshot

# Official WC 2026 draw (32 qualified teams, 12 groups)
GROUPS: dict[str, list[str]] = {
    "Group A": ["Mexico", "Jamaica", "Venezuela", "Ecuador"],
    "Group B": ["United States", "Panama", "Cuba", "Canada"],  # Canada moved to B
    "Group C": ["Uruguay", "Bolivia", "Peru", "Tahiti"],
    "Group D": ["Brazil", "Paraguay", "Chile", "DR Congo"],
    "Group E": ["Argentina", "Colombia", "Guatemala", "New Zealand"],
    "Group F": ["Portugal", "Croatia", "Morocco", "Indonesia"],
    "Group G": ["Spain", "Serbia", "Costa Rica", "Japan"],  # placeholder draw
    "Group H": ["France", "Poland", "Australia", "Saudi Arabia"],
    "Group I": ["England", "Netherlands", "Senegal", "China PR"],
    "Group J": ["Germany", "Hungary", "Algeria", "Tunisia"],
    "Group K": ["Belgium", "Ukraine", "Iran", "Cameroon"],
    "Group L": ["Italy", "Switzerland", "Nigeria", "South Korea"],
}

# Seed snapshot date — prior to tournament start (June 11, 2026)
SEED_DATE = date(2026, 6, 10)


def _zeroed_rows() -> list[StandingRow]:
    rows: list[StandingRow] = []
    for group_name, teams in GROUPS.items():
        for i, team in enumerate(teams, start=1):
            rows.append(StandingRow(
                group_name=group_name,
                team=team,
                position=i,
            ))
    return rows


def seed(session: Session) -> None:
    """Upsert the group structure skeleton into the standings table."""
    rows = _zeroed_rows()
    upsert_standings_snapshot(session, SEED_DATE, rows)
