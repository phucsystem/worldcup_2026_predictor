"""Per-match pre-kickoff forecast — DeepSeek deepseek-chat estimates a
win/draw/win split and the factors driving it for ONE upcoming match.

The fact bundle (`build_match_forecast_facts`) is pure and is the ONLY thing
handed to the model: it carries the two teams' current group-standings facts
(position, points, W/D/L record, goals, qualification) and nothing else — in
particular NOT this fixture's own scoreline — so the model estimates from
standing context without being handed the result. Percentages are a model
estimate (no deterministic ground truth exists pre-match); factor `why` lines
must cite a provided fact. Generation is keep-last-good (a failed/empty call
never clears a stored forecast)."""
from __future__ import annotations

import json
import logging
from typing import Any, Literal, Optional

from pydantic import BaseModel

log = logging.getLogger(__name__)

FORECAST_MODEL = "deepseek-chat"


class ForecastFactor(BaseModel):
    name: str
    lean: Literal["home", "away", "even"]
    why: str


class MatchForecast(BaseModel):
    home_pct: int
    draw_pct: int
    away_pct: int
    factors: list[ForecastFactor]


def _standings_facts(row) -> Optional[dict]:
    """Pull the grounding facts for one team from its StandingRow, or None when
    the team has no standings row (e.g. a knockout match)."""
    if row is None:
        return None
    return {
        "team": getattr(row, "team", None),
        "position": getattr(row, "position", None),
        "points": getattr(row, "points", None),
        "played": getattr(row, "played", None),
        "won": getattr(row, "won", None),
        "drawn": getattr(row, "drawn", None),
        "lost": getattr(row, "lost", None),
        "goals_for": getattr(row, "gf", None),
        "goals_against": getattr(row, "ga", None),
        "goal_difference": getattr(row, "gd", None),
        "qualification": getattr(row, "qualification", None),
    }


def build_match_forecast_facts(
    *,
    home_team: Optional[str],
    away_team: Optional[str],
    home_row,
    away_row,
    group_name: Optional[str],
) -> Optional[dict]:
    """Compact, deterministic fact bundle for one upcoming match, or None when
    either side lacks a standings row (nothing to ground a forecast on).
    `home_row`/`away_row` are the teams' StandingRow from the match's group."""
    home = _standings_facts(home_row)
    away = _standings_facts(away_row)
    if home is None or away is None:
        return None
    return {
        "group_name": group_name,
        "home_team": home_team,
        "away_team": away_team,
        "home_standings": home,
        "away_standings": away,
    }


def _normalize_pcts(home: int, draw: int, away: int) -> tuple[int, int, int]:
    """Clamp to non-negative and force the three values to sum to 100, absorbing
    any rounding remainder into the largest bucket. Falls back to an even-ish
    split if the model returned all zeros."""
    home, draw, away = max(0, home), max(0, draw), max(0, away)
    total = home + draw + away
    if total == 0:
        return 34, 33, 33
    vals = [round(home * 100 / total), round(draw * 100 / total), round(away * 100 / total)]
    remainder = 100 - sum(vals)
    vals[vals.index(max(vals))] += remainder
    return vals[0], vals[1], vals[2]


def generate_match_forecast(facts: dict) -> Optional[tuple[dict, str]]:
    """Generate the forecast from a fact bundle. Returns (forecast_dict, model)
    on success or None on any failure / empty output — the caller treats None as
    keep-last-good (no write). Mirrors the verdict's retry-twice pattern. The
    returned dict matches the frontend Forecast shape (home_pct/draw_pct/away_pct
    + factors[{name, lean, why}])."""
    from app.llm.deepseek import make_structured_client
    from app.pipeline.prompts import FORECAST_SYSTEM, FORECAST_USER

    user_msg = FORECAST_USER.format(facts_json=json.dumps(facts, indent=2, default=str))
    client = make_structured_client(MatchForecast)

    for _ in range(2):
        try:
            result: dict[str, Any] = client.invoke([
                {"role": "system", "content": FORECAST_SYSTEM},
                {"role": "user", "content": user_msg},
            ])
            parsed: MatchForecast = result["parsed"]
            if not parsed.factors:
                continue
            home, draw, away = _normalize_pcts(parsed.home_pct, parsed.draw_pct, parsed.away_pct)
            forecast = {
                "home_pct": home,
                "draw_pct": draw,
                "away_pct": away,
                "factors": [f.model_dump() for f in parsed.factors],
            }
            return forecast, FORECAST_MODEL
        except Exception as exc:  # noqa: BLE001 — keep-last-good: log and retry/skip
            log.warning("Forecast generation attempt failed: %s", exc)
    return None
