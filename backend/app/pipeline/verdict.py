"""Per-match verdict — DeepSeek deepseek-chat narrates a neutral factual recap of
ONE finished match from a pre-computed fact bundle.

The fact bundle (`build_match_verdict_facts`) is pure and is the ONLY thing handed
to the model: it can only restate facts derived deterministically from the score,
goal events, and the group standings — it cannot invent. Generation is
keep-last-good (a failed/empty call never clears a stored verdict)."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel

log = logging.getLogger(__name__)

VERDICT_MODEL = "deepseek-chat"


class Verdict(BaseModel):
    text: str


def _scoring_side(event) -> Optional[str]:
    """The side credited with a goal — an own goal credits the opponent."""
    side = getattr(event, "side", None)
    if side is None:
        return None
    if (getattr(event, "detail", None) or "").strip().lower() == "own goal":
        return "away" if side == "home" else "home"
    return side


def build_match_verdict_facts(
    *,
    home_team: Optional[str],
    away_team: Optional[str],
    home_score: Optional[int],
    away_score: Optional[int],
    events,
    group_name: Optional[str],
    group_rows,
) -> dict:
    """Compact, deterministic fact bundle for one finished match. `events` is the
    normalized MatchEvent list (app.api.fixtures.normalize_events); `group_rows`
    are the match's group StandingRow list (empty for knockout / no group)."""
    hs = home_score or 0
    as_ = away_score or 0
    if hs > as_:
        result, winner = "home_win", home_team
    elif hs < as_:
        result, winner = "away_win", away_team
    else:
        result, winner = "draw", None

    scorers = []
    for e in events or []:
        if (getattr(e, "type", None) or "").strip().lower() != "goal":
            continue
        credited = _scoring_side(e)
        team = home_team if credited == "home" else away_team if credited == "away" else None
        scorers.append({
            "player": getattr(e, "player", None),
            "team": team,
            "minute": getattr(e, "minute", None),
            "own_goal": (getattr(e, "detail", None) or "").strip().lower() == "own goal",
        })

    standings = [
        {
            "position": getattr(r, "position", None),
            "team": getattr(r, "team", None),
            "points": getattr(r, "points", None),
            "qualification": getattr(r, "qualification", None),
        }
        for r in (group_rows or [])
    ]

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_score": hs,
        "away_score": as_,
        "result": result,
        "winner": winner,
        "scorers": scorers,
        "group_name": group_name,
        "group_standings": standings,
    }


def generate_match_verdict(facts: dict) -> Optional[tuple[str, str]]:
    """Generate the verdict text from a fact bundle. Returns (text, model) on
    success or None on any failure / empty output — the caller treats None as
    keep-last-good (no write). Mirrors the editor node's retry-twice pattern."""
    from app.llm.deepseek import make_structured_client
    from app.pipeline.prompts import VERDICT_SYSTEM, VERDICT_USER

    user_msg = VERDICT_USER.format(facts_json=json.dumps(facts, indent=2, default=str))
    client = make_structured_client(Verdict)

    for _ in range(2):
        try:
            result: dict[str, Any] = client.invoke([
                {"role": "system", "content": VERDICT_SYSTEM},
                {"role": "user", "content": user_msg},
            ])
            parsed: Verdict = result["parsed"]
            text = (parsed.text or "").strip()
            if text:
                return text, VERDICT_MODEL
        except Exception as exc:  # noqa: BLE001 — keep-last-good: log and retry/skip
            log.warning("Verdict generation attempt failed: %s", exc)
    return None
