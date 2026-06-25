"""Shared contract + plumbing for social sources.

`Candidate` is the normalized post handed to the curation step. `SocialSource`
is the adapter protocol. The helpers (`build_query`, `dedupe`, `pretrim`,
`is_http_url`) are pure so the source adapters stay thin and testable."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel

# Shared timeout for every social network call. Explicit so a hung socket can
# never stall the daily batch (the per-source try/except catches exceptions, not
# hangs). Mirrors the bounded-timeout style of app/data/api_football.py.
HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class Candidate(BaseModel):
    """One fetched item, normalized across sources, before LLM curation."""
    source: str          # "reddit" | "bluesky" | "x" | "news"
    url: str
    author: str          # handle (social) or publication name (news)
    posted_at: Optional[str] = None   # UTC ISO-8601
    text: str
    engagement: int = 0  # upvotes/likes+reposts (social); 0 for news


@runtime_checkable
class SocialSource(Protocol):
    name: str

    def available(self) -> bool:
        """True when credentials are configured; False → the source is skipped."""
        ...

    def fetch(self, home: str, away: str, since: datetime) -> list[Candidate]:
        """Return recent candidate posts about this fixture, or [] on any failure."""
        ...


def build_query(home: str, away: str) -> str:
    """The shared search string for a fixture's social chatter."""
    return f"{home} {away} World Cup"


def is_http_url(url: Optional[str]) -> bool:
    """Accept only http(s) urls — blocks javascript:/data: and other schemes from
    ever reaching storage or the page (first of two checks; the second is render)."""
    return bool(url) and url.lower().startswith(("http://", "https://"))


def _norm_text(text: str) -> str:
    return " ".join(text.lower().split())


def dedupe(candidates: list[Candidate]) -> list[Candidate]:
    """Drop duplicates by url, then by case/whitespace-folded text (cross-source).
    Keeps the first occurrence; on a text collision keeps the higher-engagement one."""
    by_url: dict[str, Candidate] = {}
    for c in candidates:
        key = c.url.rstrip("/").lower()
        if key not in by_url:
            by_url[key] = c
    out: list[Candidate] = []
    seen_text: dict[str, int] = {}
    for c in by_url.values():
        tkey = _norm_text(c.text)
        idx = seen_text.get(tkey)
        if idx is None:
            seen_text[tkey] = len(out)
            out.append(c)
        elif c.engagement > out[idx].engagement:
            out[idx] = c
    return out


def pretrim(candidates: list[Candidate], cap: int) -> list[Candidate]:
    """Highest-engagement-first, capped — keeps the LLM input bounded."""
    return sorted(candidates, key=lambda c: c.engagement, reverse=True)[:cap]
