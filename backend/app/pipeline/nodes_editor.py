"""Editor node — DeepSeek deepseek-chat. intelligence → {title, summary, body_md}."""
from __future__ import annotations

import json
import time
from typing import Optional

from pydantic import BaseModel

from app.pipeline.state import BriefState


class Article(BaseModel):
    title: str
    summary: str
    body_md: str


def editor_node(state: BriefState) -> BriefState:
    from app.llm.deepseek import estimate_cost, make_structured_client, usage_from_raw
    from app.pipeline.prompts import EDITOR_SYSTEM, EDITOR_USER

    if state.get("error"):
        return state

    t0 = time.perf_counter()
    intelligence = state["intelligence"]
    intelligence_json = json.dumps(intelligence, indent=2)
    user_msg = EDITOR_USER.format(intelligence_json=intelligence_json)

    client = make_structured_client(Article)

    article: Optional[Article] = None
    last_exc: Optional[Exception] = None
    new_in = new_out = 0

    for attempt in range(2):
        try:
            result = client.invoke([
                {"role": "system", "content": EDITOR_SYSTEM},
                {"role": "user", "content": user_msg},
            ])
            article = result["parsed"]
            new_in, new_out = usage_from_raw(result.get("raw"))
            break
        except Exception as exc:
            last_exc = exc

    elapsed = time.perf_counter() - t0
    timings = dict(state.get("node_timings") or {})
    timings["editor"] = round(elapsed, 3)

    if article is None:
        return {
            **state,
            "node_timings": timings,
            "error": f"editor_node failed: {last_exc}",
        }

    tok_in = (state.get("tokens_in", 0) or 0) + new_in
    tok_out = (state.get("tokens_out", 0) or 0) + new_out

    return {
        **state,
        "article": article.model_dump(),
        "node_timings": timings,
        "tokens_in": tok_in,
        "tokens_out": tok_out,
        "cost_usd": estimate_cost(tok_in, tok_out),
        "error": None,
    }
