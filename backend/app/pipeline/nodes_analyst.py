"""Analyst node — DeepSeek deepseek-chat. computed_facts → structured intelligence JSON."""
from __future__ import annotations

import json
import time
from typing import Optional

from pydantic import BaseModel

from app.pipeline.state import BriefState


class Intelligence(BaseModel):
    storylines: list[str]
    surprise_teams: list[str]
    underperformers: list[str]
    power_ranking: list[str]
    qualification_narrative: str


def analyst_node(state: BriefState) -> BriefState:
    from app.llm.deepseek import estimate_cost, make_structured_client, usage_from_raw
    from app.pipeline.prompts import ANALYST_SYSTEM, ANALYST_USER

    t0 = time.perf_counter()
    facts = state["computed_facts"]
    brief_date = state["brief_date"]

    facts_json = json.dumps(facts, indent=2)
    user_msg = ANALYST_USER.format(brief_date=brief_date, facts_json=facts_json)

    client = make_structured_client(Intelligence)

    intelligence: Optional[Intelligence] = None
    last_exc: Optional[Exception] = None
    new_in = new_out = 0

    for attempt in range(2):
        try:
            result = client.invoke([
                {"role": "system", "content": ANALYST_SYSTEM},
                {"role": "user", "content": user_msg},
            ])
            intelligence = result["parsed"]
            new_in, new_out = usage_from_raw(result.get("raw"))
            break
        except Exception as exc:
            last_exc = exc

    elapsed = time.perf_counter() - t0
    timings = dict(state.get("node_timings") or {})
    timings["analyst"] = round(elapsed, 3)

    if intelligence is None:
        return {
            **state,
            "node_timings": timings,
            "error": f"analyst_node failed: {last_exc}",
        }

    tok_in = (state.get("tokens_in", 0) or 0) + new_in
    tok_out = (state.get("tokens_out", 0) or 0) + new_out

    return {
        **state,
        "intelligence": intelligence.model_dump(),
        "node_timings": timings,
        "tokens_in": tok_in,
        "tokens_out": tok_out,
        "cost_usd": estimate_cost(tok_in, tok_out),
        "error": None,
    }
