"""DeepSeek curation + safety filter for social highlights.

Mirrors app/pipeline/forecast.py: structured client, retry-twice, keep-last-good
(None on empty/failure). The model returns ONLY indices into the candidate list;
this module resolves the real fields by index, so a fabricated url/quote is
structurally impossible."""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel

from app.social.base import Candidate, is_http_url

log = logging.getLogger(__name__)

SOCIAL_MODEL = "deepseek-chat"

# Hard cap on the stored excerpt + the text handed to the LLM. Keeps UGC sent to
# DeepSeek/LangSmith short (RT-S1) and respects source copyright (link out for the rest).
_EXCERPT_CHARS = 280


class SelectedHighlight(BaseModel):
    index: int
    why: str


class HighlightSelection(BaseModel):
    selected: list[SelectedHighlight]


def _excerpt(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _EXCERPT_CHARS else text[: _EXCERPT_CHARS - 1].rstrip() + "…"


def _format_candidates(candidates: list[Candidate]) -> str:
    lines = []
    for i, c in enumerate(candidates):
        lines.append(f"[{i}] ({c.source}, score={c.engagement}) {_excerpt(c.text)}")
    return "\n".join(lines)


def generate_social_highlights(
    home: str, away: str, candidates: list[Candidate]
) -> Optional[tuple[dict, str]]:
    """Curate up to SOCIAL_HIGHLIGHTS_MAX highlights from `candidates`. Returns
    ({"highlights": [...]}, model) on success or None on empty input / no API key /
    failure / nothing selected — the caller treats None as keep-last-good (no write)."""
    from app.config import settings
    from app.llm.deepseek import make_structured_client
    from app.social.prompts import SOCIAL_SYSTEM, SOCIAL_USER

    if not candidates or not settings.DEEPSEEK_API_KEY:
        return None

    max_n = settings.SOCIAL_HIGHLIGHTS_MAX
    system = SOCIAL_SYSTEM.format(max_n=max_n)
    user = SOCIAL_USER.format(
        home=home, away=away, max_n=max_n, candidates=_format_candidates(candidates)
    )
    client = make_structured_client(HighlightSelection)

    for _ in range(2):
        try:
            result: dict[str, Any] = client.invoke([
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ])
            parsed: HighlightSelection = result["parsed"]
            highlights = _resolve(parsed.selected, candidates, max_n)
            if not highlights:
                continue
            return {"highlights": highlights}, SOCIAL_MODEL
        except Exception as exc:  # noqa: BLE001 — keep-last-good: log and retry/skip
            log.warning("Social highlight generation attempt failed: %s", exc)
    return None


def _resolve(
    selected: list[SelectedHighlight], candidates: list[Candidate], max_n: int
) -> list[dict]:
    """Map model-selected indices back to real candidate fields. Drops out-of-range
    or duplicate indices and any candidate without an http(s) url, clamps to max_n."""
    out: list[dict] = []
    seen: set[int] = set()
    for sel in selected:
        i = sel.index
        if i < 0 or i >= len(candidates) or i in seen:
            continue
        seen.add(i)
        c = candidates[i]
        if not is_http_url(c.url):
            continue
        out.append({
            "source": c.source,
            "url": c.url,
            "author": c.author,
            "posted_at": c.posted_at,
            "text": _excerpt(c.text),
            "why": sel.why,
        })
        if len(out) >= max_n:
            break
    return out
