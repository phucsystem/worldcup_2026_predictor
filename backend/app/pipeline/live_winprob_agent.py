"""Live win-prob agent — one DeepSeek call per significant event returns BOTH a
bounded win-prob adjustment AND the live-read conclusion.

The fact bundle (`build_agent_facts`) is pure and is the ONLY thing handed to the
model: the Python `compute_base` split (the anchor), the `extract_signals` bundle
(present signals only), scorers/cards so far, and team status/qualification. The
model proposes only a SMALL per-outcome adjustment — Python (`winprob.apply_adjustment`)
clamps it to base ±ADJ_BAND and re-normalizes, so it can sharpen context but never
emit a wild split. Generation is keep-last-good (a failed/empty call writes nothing)."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel

log = logging.getLogger(__name__)

LIVE_AGENT_MODEL = "deepseek-chat"


class WinProbAdjustment(BaseModel):
    home: int
    draw: int
    away: int


class LiveWinProbAgent(BaseModel):
    adjustment: WinProbAdjustment
    read: str


def _scorers_and_cards(events, home_team, away_team) -> tuple[list, list]:
    scorers, cards = [], []
    for e in events or []:
        etype = (getattr(e, "type", None) or "").strip().lower()
        side = getattr(e, "side", None)
        team = home_team if side == "home" else away_team if side == "away" else None
        if etype == "goal":
            scorers.append({
                "player": getattr(e, "player", None),
                "team": team,
                "minute": getattr(e, "minute", None),
                "own_goal": (getattr(e, "detail", None) or "").strip().lower() == "own goal",
            })
        elif etype == "card" and "red" in (getattr(e, "detail", None) or "").strip().lower():
            cards.append({
                "player": getattr(e, "player", None),
                "team": team,
                "minute": getattr(e, "minute", None),
            })
    return scorers, cards


def build_agent_facts(
    *,
    home_team: Optional[str],
    away_team: Optional[str],
    home_score: Optional[int],
    away_score: Optional[int],
    minute: Optional[int],
    status: Optional[str],
    base: dict,
    signals: dict,
    events,
    qualification: Optional[dict] = None,
) -> dict:
    """Compact, deterministic in-progress fact bundle. Carries the Python base
    (the anchor the model adjusts FROM), the present-only signals, scorers/cards,
    and an optional qualification picture. Never carries a final result — the match
    is in progress and the prompt must not frame it as decided."""
    scorers, cards = _scorers_and_cards(events, home_team, away_team)
    facts = {
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score or 0,
        "away_score": away_score or 0,
        "minute": minute or 0,
        "status": status,
        "base_win_probability": base,
        "signals": signals,
        "scorers": scorers,
        "red_cards": cards,
    }
    if qualification:
        facts["qualification"] = qualification
    return facts


def generate_live_winprob(facts: dict) -> Optional[tuple[dict, str]]:
    """Generate the bounded adjustment + live read from a fact bundle. Returns
    ({"adjustment": {home,draw,away}, "read": str}, model) on success or None on any
    failure / empty output — the caller treats None as keep-last-good (no write).
    Mirrors the verdict/forecast retry-twice pattern. The adjustment is NOT trusted
    as-is: the caller passes it through `winprob.apply_adjustment` which enforces the
    band in Python."""
    from app.llm.deepseek import make_structured_client
    from app.pipeline.prompts import LIVE_AGENT_SYSTEM, LIVE_AGENT_USER

    user_msg = LIVE_AGENT_USER.format(facts_json=json.dumps(facts, indent=2, default=str))
    client = make_structured_client(LiveWinProbAgent)

    for _ in range(2):
        try:
            result: dict[str, Any] = client.invoke([
                {"role": "system", "content": LIVE_AGENT_SYSTEM},
                {"role": "user", "content": user_msg},
            ])
            parsed: LiveWinProbAgent = result["parsed"]
            read = (parsed.read or "").strip()
            if not read:
                continue
            payload = {
                "adjustment": parsed.adjustment.model_dump(),
                "read": read,
            }
            return payload, LIVE_AGENT_MODEL
        except Exception as exc:  # noqa: BLE001 — keep-last-good: log and retry/skip
            log.warning("Live win-prob agent attempt failed: %s", exc)
    return None
