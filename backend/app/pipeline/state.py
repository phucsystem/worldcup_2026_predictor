from __future__ import annotations

from typing import Any, Optional, TypedDict


class BriefState(TypedDict):
    brief_date: str  # ISO date string YYYY-MM-DD
    matches: list[dict]
    standings: list[dict]
    computed_facts: dict[str, Any]
    intelligence: dict[str, Any]
    article: dict[str, Any]
    run_id: str
    node_timings: dict[str, float]
    tokens_in: int
    tokens_out: int
    cost_usd: float
    error: Optional[str]
